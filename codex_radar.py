#!/usr/bin/env python3
"""Codex Radar collector, four-hour cache worker, and standalone dashboard widget.

Only public benchmark metadata is requested. No account or transcript data is
sent. The degradation radar integration follows https://codexradar.com/ (2026-11-04).
Run this file directly to update the cache once; the web server owns the worker.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import re
import ssl
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen

from dashboard_assets import asset_text
from usage_common import atomic_write_json, cache_directory, ssl_context

SOURCE_URL = "https://codexradar.com/"
CACHE_VERSION = 7
REFRESH_SECONDS = 4 * 60 * 60
RETRY_SECONDS = 15 * 60
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
DEFAULT_CACHE_PATH = cache_directory() / "codex_radar_snapshot.json"
LEGACY_CACHE_PATH = Path(__file__).resolve().with_name("codex_radar_snapshot.json")
EFFORTS = ("low", "medium", "high", "xhigh", "max", "ultra")


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except OverflowError:
        return None
    return number if math.isfinite(number) else None


def iso_time(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


def source_time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Radar source timestamp is missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Radar source timestamp must include its timezone")
    return parsed.astimezone(timezone.utc)


DEGRADATION_KIND = "codex-four-task-degradation-150"
DEGRADATION_MODELS = {
    "gpt-6.1-sol": "GPT-6.1 Sol", "gpt-6-astra": "GPT-6 Astra",
    "gpt-6.1-terra": "GPT-6.1 Terra", "gpt-6-sol": "GPT-6 Sol",
    "gpt-6-luna": "GPT-6 Luna", "gpt-5.6-sol": "GPT-5.6 Sol",
    "gpt-5.6-terra": "GPT-5.6 Terra", "gpt-5.6-luna": "GPT-5.6 Luna",
}
DEGRADATION_EFFORTS = {m: EFFORTS[:-1] if "luna" in m else EFFORTS for m in DEGRADATION_MODELS}
REQUEST_TIMEOUT = 20
REQUEST_RETRY_DELAYS = (1, 3)


class DegradationPage(HTMLParser):
    """Read only the published total-score panel, never scripts or artwork."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.rows = []
        self.period = []
        self.meta = []
        self.caption = []
        self.roots = self.panels = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        parent = self.stack[-1][1] if self.stack else {}
        frame = dict(parent)
        if tag == "section" and attributes.get("id") == "stationmaster-round" and "data-intelligence-ui" in attributes:
            self.roots += 1
            frame["root"] = True
        if frame.get("root"):
            classes = attributes.get("class", "").split()
            if "cir-test-time" in classes:
                frame["text"] = self.period
            elif "cir-meta" in classes:
                # The site also uses cir-meta for grading-progress notices.
                # Keep each block separate from the task-count/score-scale heading.
                frame["text"] = []
                self.meta.append(frame["text"])
            if attributes.get("data-cir-panel") == "total":
                self.panels += 1
                frame["panel"] = True
            elif "data-cir-panel" in attributes:
                frame["panel"] = False
            if frame.get("panel"):
                if tag == "caption":
                    frame["text"] = self.caption
                if tag == "button" and "data-cir-setting" in attributes:
                    if frame.get("row") is not None:
                        raise ValueError("Nested Radar score button")
                    row = {"key": attributes["data-cir-setting"], "texts": [], "strong_count": 0}
                    self.rows.append(row)
                    frame["row"] = row
                if tag == "strong" and frame.get("row") is not None:
                    frame["row"]["strong_count"] += 1
                    frame["text"] = frame["row"]["texts"]
        if tag not in self.VOID:
            self.stack.append((tag, frame))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        if self.stack and "text" in self.stack[-1][1]:
            self.stack[-1][1]["text"].append(data)


def degradation_snapshot(html: str) -> dict[str, Any]:
    parser = DegradationPage()
    parser.feed(html)
    parser.close()
    if parser.stack or parser.roots != 1 or parser.panels != 1:
        raise ValueError("Missing, duplicate or truncated degradation score panel")
    headings = [block for block in parser.meta if re.fullmatch(
        r"\s*4\s*个分项\s*·\s*46\s*档\s*·\s*总分\s*150\s*", "".join(block))]
    if len(headings) != 1:
        raise ValueError("Degradation task set or score scale changed")
    if not re.search(r"总分\s*/\s*150", "".join(parser.caption)):
        raise ValueError("Degradation total-score scale is missing")
    period = " ".join("".join(parser.period).split())
    match = re.fullmatch(r"本轮测试[：:]\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)[–—-](\d{2}:\d{2}(?::\d{2})?)[（(]北京时间[）)]", period)
    if not match:
        raise ValueError("Degradation test period is missing or unsupported")
    start = source_time(f"{match[1]}T{match[2]}+08:00")
    end = source_time(f"{match[1]}T{match[3]}+08:00")
    if end < start:
        raise ValueError("Degradation test period is reversed")
    expected = {(m, e) for m, efforts in DEGRADATION_EFFORTS.items() for e in efforts}
    scores = {}
    for row in parser.rows:
        parts = row["key"].split(":")
        key = tuple(parts)
        if len(parts) != 2 or key not in expected or key in scores or row["strong_count"] != 1:
            raise ValueError("Invalid or duplicate degradation configuration")
        value = "".join(row["texts"]).strip()
        if value in {"—", "–", "-"}:
            score = None
        else:
            if not re.fullmatch(r"\d+(?:\.\d+)?", value):
                raise ValueError("Invalid degradation score text")
            score = float(value)
            if not math.isfinite(score) or not 0 <= score <= 150:
                raise ValueError("Degradation score outside 0–150")
        scores[key] = score
    if set(scores) != expected:
        raise ValueError("Incomplete degradation model catalog")
    return {"benchmark_kind": DEGRADATION_KIND, "source_url": SOURCE_URL + "#stationmaster-round",
            "source_started_at": start.isoformat(), "source_updated_at": end.isoformat(),
            "points": [{"model": m, "effort": e, "score": scores[m, e]}
                       for m, efforts in DEGRADATION_EFFORTS.items() for e in efforts]}


def validate_degradation_snapshot(value: Any) -> bool:
    try:
        if (set(value) != {"benchmark_kind", "source_url", "source_started_at", "source_updated_at", "points"}
                or value["benchmark_kind"] != DEGRADATION_KIND
                or value["source_url"] != SOURCE_URL + "#stationmaster-round"
                or source_time(value["source_updated_at"]) < source_time(value["source_started_at"])):
            return False
        expected = [(m, e) for m, efforts in DEGRADATION_EFFORTS.items() for e in efforts]
        if len(value["points"]) != len(expected):
            return False
        for point, key in zip(value["points"], expected):
            if set(point) != {"model", "effort", "score"} or (point["model"], point["effort"]) != key:
                return False
            if point["score"] is not None:
                score = finite_number(point["score"])
                if score is None or not 0 <= score <= 150:
                    return False
        json.dumps(value, allow_nan=False)
        return True
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def fetch_degradation(url: str) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "Codex-Usage-Dashboard/1.0", "Accept": "text/html"})
    with urlopen(request, timeout=REQUEST_TIMEOUT, context=ssl_context()) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("Radar page exceeds the size limit")
    return degradation_snapshot(raw.decode("utf-8"))


def transient_request_error(error: Exception) -> bool:
    if isinstance(error, HTTPError):
        return error.code in {502, 503, 504}
    if isinstance(error, URLError):
        return not isinstance(error.reason, ssl.SSLError) and isinstance(error.reason, (OSError, TimeoutError))
    return isinstance(error, (TimeoutError, ConnectionError)) and not isinstance(error, ssl.SSLError)


def atomic_write(path: Path, state: dict[str, Any]) -> None:
    atomic_write_json(path, state)


class RadarService:
    """A nonblocking cache reader with one bounded, server-owned refresh worker."""

    def __init__(self, cache_path: Path = DEFAULT_CACHE_PATH, *,
                 fetcher: Callable[[str], dict[str, Any]] = fetch_degradation,
                 clock: Callable[[], float] = time.time) -> None:
        self.cache_path = Path(cache_path)
        self._fetcher = fetcher
        self._clock = clock
        self._lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._stop = threading.Event()
        self._enabled = threading.Event()
        self._enabled.set()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._refreshing = False
        self._state: dict[str, Any] = {}
        now = self._clock()
        try:
            read_path = self.cache_path
            if read_path == DEFAULT_CACHE_PATH and not read_path.exists():
                read_path = LEGACY_CACHE_PATH
            state = json.loads(read_path.read_text(encoding="utf-8"))
            # json.loads accepts NaN/Infinity by default, but the atomic writer
            # correctly rejects them. Reject corrupt metadata here as well, so
            # retaining a failed attempt cannot crash the background worker.
            json.dumps(state, allow_nan=False)
            if isinstance(state, dict) and state.get("schema_version") in (1, 2, 3, 4, 5, 6, CACHE_VERSION):
                snapshot = state.get("snapshot")
                if snapshot is not None and (not isinstance(snapshot, dict)
                                             or snapshot.get("benchmark_kind") != DEGRADATION_KIND):
                    # Earlier IQ and RadarBench results cannot be relabelled as degradation scores.
                    for field in ("snapshot", "fetched_at_epoch", "legacy_snapshot"):
                        state.pop(field, None)
                    state["next_attempt_at_epoch"] = now
                    state["failures"] = 0
                    snapshot = None
                fetched = finite_number(state.get("fetched_at_epoch"))
                if snapshot is None or (validate_degradation_snapshot(snapshot) and fetched is not None and 0 < fetched <= now + 60):
                    self._state = state
                    if snapshot is None:
                        self._state.pop("fetched_at_epoch", None)
        except (OSError, ValueError):
            pass
        if self._state.get("schema_version") in (1, 2, 3, 4, 5, 6):
            self._state["failures"] = 0
            self._state["next_attempt_at_epoch"] = now
            self._state["last_error"] = "Updating the Radar snapshot to the current model catalog and benchmark rules."
        # An invalid timestamp must never postpone initial recovery indefinitely.
        next_at = finite_number(self._state.get("next_attempt_at_epoch"))
        if next_at is None or not 0 < next_at <= now + REFRESH_SECONDS:
            self._state["next_attempt_at_epoch"] = now

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            state = copy.deepcopy(self._state)
            refreshing = self._refreshing
        now = self._clock()
        fetched = finite_number(state.get("fetched_at_epoch"))
        data = state.get("snapshot")
        age = max(0, now - fetched) if fetched is not None else None
        return {
            "available": data is not None,
            "refreshing": refreshing,
            "stale": data is not None and (age is None or age >= REFRESH_SECONDS or bool(state.get("last_error"))),
            "age_seconds": int(age) if age is not None else None,
            "fetched_at": iso_time(fetched) if fetched is not None else None,
            "next_attempt_at": iso_time(state.get("next_attempt_at_epoch", now)),
            "refresh_seconds": REFRESH_SECONDS,
            "last_error": state.get("last_error"),
            "cache_warning": state.get("cache_warning"),
            "data": data,
        }

    def refresh_if_due(self, *, force: bool = False) -> bool:
        if not self._enabled.is_set():
            return False
        if not self._refresh_lock.acquire(blocking=False):
            return False
        try:
            now = self._clock()
            with self._lock:
                if not force and now < self._state.get("next_attempt_at_epoch", 0):
                    return False
                previous = copy.deepcopy(self._state)
                self._refreshing = True
            try:
                data = self._fetch_with_retry()
                if not validate_degradation_snapshot(data):
                    raise ValueError("Invalid degradation radar snapshot")
                prior_data = previous.get("snapshot")
                if prior_data and source_time(data["source_updated_at"]) < source_time(prior_data["source_updated_at"]):
                    raise ValueError("Radar page is older than the last successful snapshot")
                finished = self._clock()
                state = {"snapshot": data, "fetched_at_epoch": finished,
                         "failures": 0, "next_attempt_at_epoch": finished + REFRESH_SECONDS}
            except Exception as exc:
                old_failures = finite_number(previous.get("failures")) or 0
                failures = max(0, min(int(old_failures), 4)) + 1
                delay = min(REFRESH_SECONDS, RETRY_SECONDS * 2 ** (failures - 1))
                state = {**previous, "failures": failures,
                         "last_error": f"{type(exc).__name__}: {exc}"[:300],
                         "next_attempt_at_epoch": self._clock() + delay}
            state.update(schema_version=CACHE_VERSION, last_attempt_at_epoch=now)
            state.pop("cache_warning", None)
            try:
                atomic_write(self.cache_path, state)
            except OSError:
                state["cache_warning"] = "Could not save the Radar cache to disk."
            with self._lock:
                self._state = state
            return not bool(state.get("last_error"))
        finally:
            with self._lock:
                self._refreshing = False
            self._refresh_lock.release()

    def _fetch_with_retry(self) -> dict[str, Any]:
        for attempt in range(len(REQUEST_RETRY_DELAYS) + 1):
            if self._stop.is_set() or not self._enabled.is_set():
                raise RuntimeError("Radar refresh stopped")
            try:
                return self._fetcher(SOURCE_URL)
            except Exception as exc:
                if isinstance(exc, HTTPError):
                    exc.close()
                if not transient_request_error(exc) or attempt == len(REQUEST_RETRY_DELAYS):
                    raise
                # Stop/pause wakes retry waits; never launches another request while disabled.
                self._wake.wait(REQUEST_RETRY_DELAYS[attempt])
                self._wake.clear()
        raise RuntimeError("Radar retry limit exceeded")

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="codex-radar-refresh", daemon=True)
        self._thread.start()

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            self._enabled.set()
        else:
            self._enabled.clear()
        self._wake.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._wake.clear()
            self.refresh_if_due()
            with self._lock:
                remaining = self._state.get("next_attempt_at_epoch", 0) - self._clock()
            # Recheck wall-clock deadlines after waking from system sleep.
            self._wake.wait(min(60, max(0.1, remaining)) if self._enabled.is_set() else 60)

    def close(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=1)


STYLE = asset_text("static/radar.css")

SCRIPT = asset_text("static/radar.js")


# Keep the score renderer model/effort catalog aligned with collection.
SCRIPT = SCRIPT.replace("__RADAR_BENCH_EFFORTS__", json.dumps(DEGRADATION_EFFORTS))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE_PATH)
    parser.add_argument("--force", action="store_true", help="Refresh even if the four-hour cache is still fresh.")
    args = parser.parse_args()
    service = RadarService(args.cache)
    service.refresh_if_due(force=args.force)
    result = service.snapshot()
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    raise SystemExit(1 if result["last_error"] else 0)


if __name__ == "__main__":
    main()
