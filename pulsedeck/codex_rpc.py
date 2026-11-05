"""Read-only Codex app-server adapter, with a bounded per-process cache."""
from __future__ import annotations

import copy
import json
import math
import os
import queue
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

_lock = threading.Lock()
_cached = None
_expires = 0.0

def find_binary() -> Path | None:
    candidates = [os.environ.get("CODEX_BIN"), shutil.which("codex")]
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    installed = list((local / "OpenAI/Codex/bin").glob("*/codex.exe"))
    candidates.extend(sorted(installed, key=lambda p: p.stat().st_mtime, reverse=True))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    return None

def read_account(binary: Path) -> dict:
    """Only initialize and account read methods; never starts a model turn."""
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        [str(binary), "app-server", "--listen", "stdio://"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", creationflags=flags,
    )
    messages = queue.Queue(maxsize=64)
    def receive():
        try:
            for line in process.stdout:
                try:
                    value = json.loads(line)
                    messages.put_nowait(value)
                except (ValueError, queue.Full):
                    continue
        finally:
            try:
                messages.put_nowait(None)
            except queue.Full:
                pass
    reader = threading.Thread(target=receive, daemon=True)
    reader.start()
    deadline = time.monotonic() + 20
    sequence = 0
    def send(value):
        process.stdin.write(json.dumps(value) + "\n")
        process.stdin.flush()
    def request(method, params=None):
        nonlocal sequence
        sequence += 1
        send({"id": sequence, "method": method, "params": params or {}})
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Codex account query timed out.")
            try:
                value = messages.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError("Codex account query timed out.") from None
            if value is None:
                raise OSError("Codex app-server exited before replying.")
            if value.get("id") != sequence:
                continue
            if "error" in value:
                # Do not propagate provider error bodies that might contain account data.
                raise OSError(f"Codex does not currently support {method}.")
            result = value.get("result")
            if not isinstance(result, dict):
                raise ValueError("Invalid Codex account response.")
            return result
    try:
        request("initialize", {"clientInfo": {"name": "pulsedeck", "title": "PulseDeck",
                                             "version": "0.1.0"}})
        send({"method": "initialized"})
        limits = request("account/rateLimits/read")
        try:
            usage = request("account/usage/read")
        except (OSError, ValueError, TimeoutError):
            usage = {}
        return {"limits": limits, "usage": usage}
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        reader.join(timeout=1)
        process.stdout.close()

def account_snapshot() -> dict | None:
    global _cached, _expires
    if os.environ.get("PULSEDECK_CODEX_TRANSPORT", "auto") == "legacy":
        return None
    with _lock:
        if time.monotonic() < _expires:
            return copy.deepcopy(_cached)
        binary = find_binary()
        try:
            value = read_account(binary) if binary else None
        except (OSError, ValueError, TimeoutError):
            value = None
        _cached = value
        _expires = time.monotonic() + 60
        return copy.deepcopy(value)

def number(value):
    return value if not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) else None

def window(value, now):
    if not isinstance(value, dict):
        return None
    used, reset, minutes = (number(value.get(k)) for k in ("usedPercent", "resetsAt", "windowDurationMins"))
    if used is None and reset is None:
        return None
    return {"used_percent": used, "reset_at": reset,
            "reset_after_seconds": max(0, reset - now) if reset is not None else None,
            "limit_window_seconds": minutes * 60 if minutes is not None else None}

def online_report(snapshot: dict) -> dict:
    now = time.time()
    limits = snapshot.get("limits", {})
    buckets = limits.get("rateLimitsByLimitId") or {}
    # Never silently label a different metered bucket as Codex.
    rate = buckets.get("codex") or limits.get("rateLimits") or {}
    if rate.get("limitId") not in (None, "codex"):
        rate = {}
    primary, secondary = window(rate.get("primary"), now), window(rate.get("secondary"), now)
    used = [w["used_percent"] for w in (primary, secondary) if w and w["used_percent"] is not None]
    reached = True if rate.get("rateLimitReachedType") else (any(p >= 100 for p in used) if used else None)
    credits = rate.get("credits") or {}
    summary = snapshot.get("usage", {}).get("summary") or {}
    stats = {target: summary.get(source) for source, target in (
        ("lifetimeTokens", "lifetime_tokens"), ("peakDailyTokens", "peak_daily_tokens"),
        ("longestRunningTurnSec", "longest_running_turn_sec"),
        ("currentStreakDays", "current_streak_days"))}
    data = {"plan_type": rate.get("planType"),
            "rate_limit": {"primary_window": primary, "secondary_window": secondary,
                           "limit_reached": reached},
            "credits": {"balance": credits.get("balance"), "has_credits": credits.get("hasCredits"),
                        "unlimited": credits.get("unlimited")}}
    return {"retrieved_at_unix_ms": round(now * 1000),
            "retrieved_at_local": datetime.fromtimestamp(now).astimezone().isoformat(),
            "source": "codex_app_server",
            "endpoints": {
                "rate_limit_status": {"ok": True, "path": "account/rateLimits/read", "data": data},
                "profile": {"ok": bool(summary), "path": "account/usage/read", "data": {"stats": stats}},
            }}

def resets_report(snapshot: dict) -> dict | None:
    credits = snapshot.get("limits", {}).get("rateLimitResetCredits")
    if not isinstance(credits, dict):
        return None  # Older clients can still use the legacy read-only endpoint.
    from codex_usage import normalise_credit_for_json
    rows = []
    for row in credits.get("credits") or []:
        if not isinstance(row, dict):
            continue
        mapped = {target: row.get(source) for source, target in (
            ("resetType", "reset_type"), ("status", "status"),
            ("grantedAt", "granted_at"), ("expiresAt", "expires_at"))}
        # Legacy normalization expects an ISO date, whereas RPC returns epoch seconds.
        for field in ("granted_at", "expires_at"):
            if number(mapped[field]) is not None:
                mapped[field] = datetime.fromtimestamp(mapped[field]).astimezone().isoformat()
        rows.append(normalise_credit_for_json(mapped))
    return {"ok": True, "source": "codex_app_server",
            "retrieved_at_unix_ms": round(time.time() * 1000),
            "available_count": credits.get("availableCount"), "credits_returned": len(rows),
            "total_earned_count": None, "credits": rows}
