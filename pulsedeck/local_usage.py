"""Incremental, metadata-only local usage index for Codex and Claude."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import threading

CODEX_FIELDS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                "output_tokens", "reasoning_output_tokens", "total_tokens")
CLAUDE_FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens",
                 "cache_read_input_tokens", "total_tokens")
RANGES = frozenset({"today", "7d", "30d", "all"})
UNKNOWN = "(unknown)"


def timestamp(value):
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)) and math.isfinite(value):
            return datetime.fromtimestamp(value, timezone.utc)
        if isinstance(value, str) and value.strip():
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed
    except (ValueError, OSError, OverflowError):
        pass
    return None


def counts(value, source):
    if not isinstance(value, dict):
        return None
    fields = CODEX_FIELDS if source == "codex" else CLAUDE_FIELDS
    result = {k: int(v) for k, v in value.items() if k in fields
              and isinstance(v, (int, float)) and not isinstance(v, bool)
              and 0 <= v <= 2**53 - 1 and math.isfinite(v) and int(v) == v}
    if source == "claude":
        if not result:
            return None
        result["total_tokens"] = sum(result.get(k, 0) for k in CLAUDE_FIELDS[:-1])
    elif "total_tokens" not in result and "input_tokens" in result and "output_tokens" in result:
        result["total_tokens"] = result["input_tokens"] + result["output_tokens"]
    return result if "total_tokens" in result else None


def signature(usage):
    return tuple(sorted((usage or {}).items()))


def short_project(value):
    if not value:
        return "-"
    text = str(value).replace(str(Path.home()), "~", 1)
    return text if len(text) <= 80 else "…/" + text.replace("\\", "/").rstrip("/").split("/")[-1]


@dataclass(frozen=True)
class TimeScope:
    name: str = "all"
    anchor: date = field(default_factory=date.today)
    tz: object = None

    def __post_init__(self):
        if self.name not in RANGES:
            raise ValueError("range must be today, 7d, 30d, or all")

    @property
    def start(self):
        days = {"today": 1, "7d": 7, "30d": 30}.get(self.name)
        return self.anchor - timedelta(days=days - 1) if days else None

    def includes(self, when):
        if when is None:
            return self.name == "all"
        day = self.day(when)
        return day <= self.anchor and (self.start is None or day >= self.start)

    def day(self, when):
        return when.astimezone(self.tz).date()

    def as_dict(self):
        return {"range": self.name, "start": self.start.isoformat() if self.start else None,
                "end": self.anchor.isoformat(), "timezone": "local",
                "unknown_dates_included": self.name == "all"}


def make_scope(name="all", anchor=None):
    if isinstance(anchor, str):
        anchor = date.fromisoformat(anchor)
    return TimeScope(name, anchor or date.today())


class CodexParser:
    def __init__(self, path):
        self.path = path
        self.session = path.stem
        self.turn = None
        self.model = UNKNOWN
        self.project = None
        self.provider = None
        self.points = []
        self.endpoints = {}
        self.responses = {}
        self.duplicates = 0
        self.lines = 0
        self.errors = 0
        self.latest_cumulative = None

    def consume(self, obj):
        if not isinstance(obj, dict):
            return
        kind = obj.get("type")
        if kind is not None and not isinstance(kind, str):
            return
        payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else obj
        subtype = payload.get("type")
        if subtype is not None and not isinstance(subtype, str):
            return
        if kind == "compacted":
            self.endpoints.clear()
            return
        if kind == "session_meta":
            self.session = str(payload.get("id") or payload.get("thread_id") or self.session)
        if kind in {"session_meta", "turn_context"} or subtype in {"task_started", "thread_settings_applied"} or kind is None:
            turn = payload.get("turn_id")
            if turn and turn != self.turn:
                self.turn, self.model = str(turn), UNKNOWN
            if isinstance(payload.get("model"), str):
                self.model = payload["model"] or UNKNOWN
            if isinstance(payload.get("cwd"), str):
                self.project = payload["cwd"]
            if isinstance(payload.get("model_provider"), str):
                self.provider = payload["model_provider"]

        direct = kind == "token_usage_record"
        info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
        if not direct and subtype != "token_count" and not (kind is None and info):
            return
        cumulative = counts(payload.get("thread_token_usage") if direct else info.get("total_token_usage"), "codex")
        actual = counts(payload.get("usage"), "codex") if direct else None
        last = counts(info.get("last_token_usage"), "codex") if not direct else None
        if cumulative is None and actual is None:
            return
        if cumulative and not direct:
            if self.latest_cumulative is not None and cumulative["total_tokens"] < self.latest_cumulative:
                self.endpoints.clear()
            self.latest_cumulative = cumulative["total_tokens"]
        turn = str(payload.get("turn_id") or self.turn or "")
        model = payload.get("model") or (self.model if not self.turn or turn == self.turn else UNKNOWN)
        response = str(payload.get("response_id") or "") if direct else ""
        endpoint = (direct, turn, signature(cumulative)) if cumulative is not None else None
        index = self.responses.get(response) if response else None
        if index is None and endpoint is not None:
            index = self.endpoints.get(endpoint)
            if direct and index is not None and self.points[index].get("response") not in ("", response):
                index = None
        point = {"cumulative": cumulative, "actual": actual, "last": last,
                 "timestamp": timestamp(obj.get("timestamp") or payload.get("timestamp")),
                 "turn": turn, "model": str(model or UNKNOWN), "project": self.project,
                 "session": str(payload.get("thread_id") or self.session), "response": response,
                 "file": str(self.path)}
        if index is not None:
            old = self.points[index]
            self.duplicates += 1
            # Direct per-response evidence supersedes its duplicate cumulative display event.
            if actual and (not old["actual"] or actual["total_tokens"] >= old["actual"]["total_tokens"]):
                if old["timestamp"] and point["timestamp"]:
                    point["timestamp"] = min(old["timestamp"], point["timestamp"])
                if point["model"] == UNKNOWN:
                    point["model"] = old["model"]
                self.points[index] = point
            elif old["actual"] is None and old["last"] is None and last:
                old["last"] = last
            if response:
                self.responses[response] = index
            if endpoint is not None:
                self.endpoints[endpoint] = index
            return
        index = len(self.points)
        self.points.append(point)
        if endpoint is not None:
            self.endpoints[endpoint] = index
        if response:
            self.responses[response] = index

    def records(self):
        # thread_token_usage can restart with the process while token_count keeps
        # historical totals. Never subtract counters belonging to these streams.
        direct_by_usage, direct_by_counter = defaultdict(list), defaultdict(list)
        for i, point in enumerate(self.points):
            if point["actual"] is not None:
                normalized = tuple(point["actual"].get(k, 0) for k in CODEX_FIELDS)
                direct_by_usage[(point["turn"], normalized)].append(i)
                if point["cumulative"]:
                    direct_by_counter[(point["turn"], signature(point["cumulative"]))].append(i)
        pairs, paired = {}, set()
        for i, point in enumerate(self.points):
            if point["actual"] is not None:
                continue
            candidates = direct_by_usage.get((point["turn"], tuple((point["last"] or {}).get(k, 0) for k in CODEX_FIELDS)), [])
            if not candidates:
                candidates = direct_by_counter.get((point["turn"], signature(point["cumulative"])), [])
            available = [j for j in candidates if j not in paired]
            if available:
                match = min(available, key=lambda j: abs(j - i))
                pairs[i] = match
                paired.add(match)
        self.paired_duplicates = len(pairs)
        covered_ahead = {j for i, j in pairs.items() if j > i}
        previous, epoch, resets = None, 0, 0
        direct_since_snapshot = Counter()
        output = []
        for i, point in enumerate(self.points):
            cumulative, actual, last = point["cumulative"], point["actual"], point["last"]
            if actual is not None:
                usage = {k: actual.get(k, 0) for k in CODEX_FIELDS}
                if i not in covered_ahead:
                    direct_since_snapshot.update(usage)
                key = ("response:" + point["response"] if point["response"] else
                       "direct:" + (point["turn"] or point["session"]) + ":" + repr(signature(cumulative or actual)))
                output.append({**point, "key": key, "usage": usage, "basis": "request"})
                continue
            if cumulative is None:
                continue
            had_previous = previous is not None
            reset = bool(previous and cumulative["total_tokens"] < previous["total_tokens"])
            if reset:
                epoch += 1
                resets += 1
            baseline = {} if previous is None or reset else previous
            match = pairs.get(i)
            if match is not None and match > i:
                direct_since_snapshot.update(self.points[match]["actual"])
            delta = {k: max(0, cumulative.get(k, baseline.get(k, 0)) - baseline.get(k, 0)
                            - direct_since_snapshot.get(k, 0)) for k in CODEX_FIELDS}
            previous = cumulative
            direct_since_snapshot.clear()
            if not delta["total_tokens"]:
                continue
            identity = "counter:" + (point["turn"] or point["session"]) + ":" + str(epoch) + ":" + repr(signature(cumulative))
            if match is None and last is not None:
                usage = {k: min(last.get(k, 0), delta[k]) for k in CODEX_FIELDS}
            elif match is None and had_previous and not reset:
                usage = delta
            else:
                usage = {}
            if usage.get("total_tokens", 0):
                output.append({**point, "key": identity, "usage": usage, "basis": "cumulative_delta"})
            gap = {k: max(0, delta[k] - usage.get(k, 0)) for k in CODEX_FIELDS}
            if gap["total_tokens"]:
                output.append({**point, "key": identity + ":unattributed", "usage": gap,
                               "timestamp": None, "model": UNKNOWN, "project": None, "basis": "unattributed_baseline"})
        return output, resets


class ClaudeParser:
    def __init__(self, path):
        self.path = path
        self.rows = {}
        self.duplicates = 0
        self.lines = 0
        self.errors = 0

    def consume(self, obj):
        if not isinstance(obj, dict) or obj.get("type") != "assistant":
            return
        message = obj.get("message")
        if not isinstance(message, dict):
            return
        usage = counts(message.get("usage"), "claude")
        if not usage or usage["total_tokens"] <= 0:
            return
        message_id, request = str(message.get("id") or ""), str(obj.get("requestId") or "")
        session = str(obj.get("sessionId") or self.path.stem)
        when = timestamp(obj.get("timestamp"))
        model = str(message.get("model") or UNKNOWN)
        key = ("message:" + message_id if message_id else "request:" + request) if message_id or request else (
            "fallback:" + session + "|" + str(obj.get("timestamp")) + "|" + model + "|" + repr(signature(usage)))
        row = {"key": key, "session": session, "timestamp": when, "model": model,
               "project": obj.get("cwd") if isinstance(obj.get("cwd"), str) else None,
               "usage": {k: usage.get(k, 0) for k in CLAUDE_FIELDS}, "file": str(self.path), "basis": "request"}
        old = self.rows.get(key)
        if old:
            self.duplicates += 1
            # Streaming repeats may carry a later, more complete output counter.
            if old["usage"]["total_tokens"] > row["usage"]["total_tokens"]:
                row["usage"] = old["usage"]
            if old["timestamp"] and row["timestamp"]:
                row["timestamp"] = min(old["timestamp"], row["timestamp"])
            row["project"] = row["project"] or old["project"]
        self.rows[key] = row

    def records(self):
        return list(self.rows.values()), 0


@dataclass
class FileState:
    parser: object
    identity: tuple
    size: int = 0
    mtime: int = 0
    offset: int = 0
    head: bytes = b""
    tail: bytes = b""
    head_length: int = 0
    tail_length: int = 0
    unterminated: bool = False


class IncrementalIndex:
    """Keep only metadata and hash anchors; never cache conversation text."""
    def __init__(self, parser_type):
        self.parser_type = parser_type
        self.entries = {}
        self.lock = threading.Lock()

    @staticmethod
    def _hash(handle, start, length, metrics):
        handle.seek(start)
        data = handle.read(length)
        metrics["bytes_read"] += len(data)
        return hashlib.sha256(data).digest()

    def scan(self, files):
        metrics = {"bytes_read": 0, "lines_parsed": 0, "files_rebuilt": 0,
                   "files_appended": 0, "files_reused": 0, "read_errors": 0, "pending_lines": 0}
        live = {str(path) for path in files}
        # Each source index is scoped to the single root passed by the collector.
        for key in set(self.entries) - live:
            del self.entries[key]
        states = []
        for path in files:
            key = str(path)
            state = self.entries.get(key)
            try:
                stat = path.stat()
                identity = (stat.st_dev, stat.st_ino)
                if state and (state.identity, state.size, state.mtime) == (identity, stat.st_size, stat.st_mtime_ns):
                    metrics["files_reused"] += 1
                    metrics["pending_lines"] += int(state.offset < state.size)
                    states.append(state)
                    continue
                with path.open("rb") as handle:
                    stat = os.fstat(handle.fileno())
                    identity = (stat.st_dev, stat.st_ino)
                    append = bool(state and state.identity == identity and stat.st_size > state.size and not state.unterminated)
                    if append:
                        append = (self._hash(handle, 0, state.head_length, metrics) == state.head
                                  and self._hash(handle, state.offset - state.tail_length, state.tail_length, metrics) == state.tail)
                    if not append:
                        state = FileState(self.parser_type(path), identity)
                        metrics["files_rebuilt"] += 1
                    else:
                        metrics["files_appended"] += 1
                    handle.seek(state.offset)
                    while handle.tell() < stat.st_size:
                        start = handle.tell()
                        raw = handle.readline(stat.st_size - start)
                        metrics["bytes_read"] += len(raw)
                        complete = raw.endswith(b"\n")
                        try:
                            obj = json.loads(raw.decode("utf-8"))
                        except (ValueError, UnicodeError):
                            if not complete:
                                break
                            state.parser.errors += 1
                            obj = None
                        if raw.strip():
                            state.parser.lines += 1
                            metrics["lines_parsed"] += 1
                            if obj is not None:
                                state.parser.consume(obj)
                        state.offset = handle.tell()
                        state.unterminated = not complete
                    state.size, state.mtime = stat.st_size, stat.st_mtime_ns
                    state.head_length = min(256, state.offset)
                    state.tail_length = min(256, state.offset)
                    state.head = self._hash(handle, 0, state.head_length, metrics)
                    state.tail = self._hash(handle, state.offset - state.tail_length, state.tail_length, metrics)
                    self.entries[key] = state
                    metrics["pending_lines"] += int(state.offset < state.size)
                    states.append(state)
            except OSError:
                metrics["read_errors"] += 1
                # Do not present cached deleted/unreadable files as freshly collected data.
        return states, metrics


CODEX_INDEX = IncrementalIndex(CodexParser)
CLAUDE_INDEX = IncrementalIndex(ClaudeParser)


def aggregate(home: Path, source: str, top: int = 10, range_name: str = "all", anchor=None):
    home = home.resolve()
    scope = make_scope(range_name, anchor)
    index = CODEX_INDEX if source == "codex" else CLAUDE_INDEX
    folders = [home / "sessions", home / "archived_sessions"] if source == "codex" else [home / "projects"]
    files = sorted({p for folder in folders if folder.exists() for p in folder.rglob("*.jsonl")})
    with index.lock:
        states, metrics = index.scan(files)
        records = {}
        duplicates = resets = parse_errors = lines = 0
        for state in states:
            rows, count = state.parser.records()
            resets += count
            duplicates += state.parser.duplicates + getattr(state.parser, "paired_duplicates", 0)
            parse_errors += state.parser.errors
            lines += state.parser.lines
            for row in rows:
                old = records.get(row["key"])
                if old:
                    duplicates += 1
                    earliest = min(t for t in (old["timestamp"], row["timestamp"]) if t is not None) if old["timestamp"] or row["timestamp"] else None
                    if old["usage"]["total_tokens"] > row["usage"]["total_tokens"]:
                        row = old
                    row = {**row, "timestamp": earliest}
                records[row["key"]] = row
        selected = [r for r in records.values() if scope.includes(r["timestamp"])]
        result = summarize(selected, source, top, scope)
        result.update(available=any(folder.exists() for folder in folders),
                      source=source, files=len(files), refresh=metrics,
                      quality={"parse_errors": parse_errors + metrics["read_errors"], "counter_resets": resets,
                               "duplicates_skipped": duplicates, "pending_lines": metrics["pending_lines"],
                               "unknown_date_tokens": sum(r["usage"]["total_tokens"] for r in records.values() if r["timestamp"] is None),
                               "unknown_model_tokens": sum(r["usage"]["total_tokens"] for r in selected if r["model"] == UNKNOWN)},
                      jsonl_lines_scanned=lines)
        return result


def summarize(records, source, top, scope):
    fields = CODEX_FIELDS if source == "codex" else CLAUDE_FIELDS
    total = Counter({key: 0 for key in fields})
    models, projects, sessions, daily = {}, {}, {}, {}
    latest = None
    for record in records:
        usage, model = record["usage"], record["model"]
        total.update(usage)
        session = record["session"]
        project = record["project"] or "-"
        for group, key in ((models, model), (projects, project), (sessions, session)):
            row = group.setdefault(key, {"usage": Counter({k: 0 for k in fields}), "requests": 0, "sessions": set(), "models": set()})
            row["usage"].update(usage)
            row["requests"] += 1
            row["sessions"].add(session)
            row["models"].add(model)
        when = record["timestamp"]
        meta = sessions[session]
        if "timestamp" not in meta or (when and (meta["timestamp"] is None or when > meta["timestamp"])):
            meta.update(timestamp=when, file=record["file"], project=project)
        if when is not None:
            latest = max(latest, when) if latest else when
            day = scope.day(when).isoformat()
            row = daily.setdefault(day, {"usage": Counter({k: 0 for k in fields}), "requests": 0, "sessions": set()})
            row["usage"].update(usage)
            row["requests"] += 1
            row["sessions"].add(session)
    ranked_models = sorted(models.items(), key=lambda item: (-item[1]["usage"]["total_tokens"], item[0]))
    model_rows = [{"model": key, **dict(row["usage"]), "tokens_used": row["usage"]["total_tokens"],
                   "requests": row["requests"], "sessions": len(row["sessions"]), "threads": len(row["sessions"]),
                   "share": row["usage"]["total_tokens"] / total["total_tokens"] * 100 if total["total_tokens"] else 0}
                  for key, row in ranked_models[:top]]
    if len(ranked_models) > top:
        remainder = ranked_models[top:]
        other = sum(row["usage"]["total_tokens"] for _, row in remainder)
        model_rows.append({"model": "__other__", "total_tokens": other, "tokens_used": other,
                           "requests": sum(row["requests"] for _, row in remainder),
                           "sessions": len(set().union(*(row["sessions"] for _, row in remainder))),
                           "threads": len(set().union(*(row["sessions"] for _, row in remainder))),
                           "share": other / total["total_tokens"] * 100, "model_count": len(remainder)})
    daily_rows = []
    dates = sorted(daily)
    if scope.start:
        dates = [(scope.start + timedelta(days=i)).isoformat() for i in range((scope.anchor - scope.start).days + 1)]
    for day in dates:
        row = daily.get(day, {"usage": Counter({k: 0 for k in fields}), "requests": 0, "sessions": set()})
        daily_rows.append({"date": day, **dict(row["usage"]), "requests": row["requests"], "sessions": len(row["sessions"])})
    project_rows = [{"project": short_project(key), **dict(row["usage"]), "requests": row["requests"], "sessions": len(row["sessions"])}
                    for key, row in sorted(projects.items(), key=lambda item: -item[1]["usage"]["total_tokens"])[:top]]
    session_rows = [{"session_file": Path(row["file"]).name, "date": scope.day(row["timestamp"]).isoformat() if row["timestamp"] else "unknown",
                     "project": short_project(row["project"]), "models": sorted(row["models"]), "model": ", ".join(sorted(row["models"])),
                     "requests": row["requests"], "usage": dict(row["usage"])}
                    for _, row in sorted(sessions.items(), key=lambda item: -item[1]["usage"]["total_tokens"])[:top]]
    return {"scope": scope.as_dict(), "token_totals": dict(total), "unique_usage_records": len(records),
            "session_count": len(sessions), "model_count": len(models), "by_model": model_rows,
            "by_project": project_rows, "daily_usage": daily_rows, "top_sessions": session_rows,
            "latest_record_at_unix_ms": int(latest.timestamp() * 1000) if latest else None}
