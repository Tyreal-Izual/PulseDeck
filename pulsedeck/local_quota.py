"""Quota snapshots already written by Codex; no account client or network calls."""
from __future__ import annotations

import math
import time


def number(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and abs(value) <= 2**53 - 1 and math.isfinite(value):
        return value
    return None


def codex_snapshot(value, captured_at):
    if not isinstance(value, dict) or captured_at is None:
        return None
    # Model-specific buckets must not replace the main Codex account window.
    if value.get("limit_id") not in (None, "", "codex"):
        return None
    result = {"captured_at_unix_ms": int(captured_at.timestamp() * 1000),
              "five_hour": None, "seven_day": None}
    if isinstance(value.get("plan_type"), str):
        result["plan_type"] = value["plan_type"]
    for field in ("primary", "secondary"):
        window = value.get(field)
        if not isinstance(window, dict):
            continue
        # A weekly-only snapshot can place the seven-day window in primary.
        key = {300: "five_hour", 10080: "seven_day"}.get(number(window.get("window_minutes")))
        if key is None:
            continue
        used, reset = number(window.get("used_percent")), number(window.get("resets_at"))
        if used is None and reset is None:
            continue
        normalized = {}
        if used is not None:
            normalized["used_percentage"] = max(0.0, min(100.0, used))
            normalized["remaining_percentage"] = 100.0 - normalized["used_percentage"]
        if reset is not None and reset > 0:
            normalized["resets_at"] = int(reset)
        result[key] = normalized or None
    return result


def quota_report(snapshot, now=None):
    now = time.time() if now is None else now
    result = {"available": False, "source": "local_session_log", "stale_after_seconds": 900,
              "five_hour": None, "seven_day": None, "network_calls_made": 0}
    if snapshot is None:
        return {**result, "reason": "snapshot_not_found"}
    age = max(0, now - snapshot["captured_at_unix_ms"] / 1000)
    result.update(snapshot, age_seconds=age, stale=age > result["stale_after_seconds"])
    result["available"] = bool(result["five_hour"] or result["seven_day"])
    for key in ("five_hour", "seven_day"):
        if result[key] is not None:
            result[key] = dict(result[key])
            reset = result[key].get("resets_at")
            if reset is not None:
                result[key]["reset_after_seconds"] = max(0, int(reset - now))
    return result
