#!/usr/bin/env python3
"""Read local Claude Code usage without modifying Claude Code data.

The collector has two independent sources:

* ``~/.claude/projects/**/*.jsonl`` for per-request token counters.
* A small rate-limit snapshot written by ``claude_usage_statusline.py``.

Only metadata and usage counters are returned. Prompt text, assistant content,
tool inputs, file contents, credentials, and transcript bodies are ignored.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from usage_common import resolve_claude_home, resolve_snapshot_path, find_claude_binary


TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)
TOTAL_FIELD = "total_tokens"
DEFAULT_STALE_SECONDS = 15 * 60
CLAUDE_AUTH_TIMEOUT_SECONDS = 5


CLAUDE_HOME = resolve_claude_home()


def local_now_text() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z %z")


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def local_timestamp_text(value: Any) -> str | None:
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z %z")


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


from pulsedeck.local_usage import CLAUDE_INDEX, aggregate as aggregate_events
_FILE_CACHE = CLAUDE_INDEX.entries


def aggregate_local_usage(claude_home: Path, top_n: int, days: int = 30, range_name: str = "all", anchor=None) -> dict[str, Any]:
    result = aggregate_events(claude_home, "claude", top_n, range_name, anchor)
    result.update(projects_dir=str(claude_home / "projects"), session_files=result["files"],
                  parse_or_read_errors=result["quality"]["parse_errors"],
                  duplicate_usage_records_skipped=result["quality"]["duplicates_skipped"],
                  usage_rows_seen=result["unique_usage_records"] + result["quality"]["duplicates_skipped"])
    return result


def stale_seconds() -> int:
    try:
        return max(60, int(os.environ.get("CLAUDE_USAGE_STALE_SECONDS", DEFAULT_STALE_SECONDS)))
    except ValueError:
        return DEFAULT_STALE_SECONDS


def statusline_script_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().with_name("claude_usage_statusline.py")
    return Path(__file__).resolve().with_name("claude_usage_statusline.py")


def statusline_install_command() -> str:
    if sys.platform == "win32":
        return str(Path(__file__).resolve().with_name("Setup-Claude-Capture.cmd"))
    return " ".join(
        [shlex.quote(sys.executable), shlex.quote(str(statusline_script_path())), "--install"]
    )


def statusline_is_installed(claude_home: Path) -> bool:
    settings_path = claude_home / "settings.json"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    status_line = settings.get("statusLine") if isinstance(settings, dict) else None
    if not isinstance(status_line, dict):
        return False
    command = str(status_line.get("command") or "")
    normalized = command.replace("\\", "/")
    script = statusline_script_path()
    return any(path.as_posix() in normalized for path in (
        script, script.parent / "scripts" / "capture-claude.ps1"))


def claude_binary_path() -> str | None:
    path = find_claude_binary()
    return str(path) if path else None


def claude_auth_status() -> dict[str, Any]:
    return {"checked": False, "logged_in": None, "requires_login": False, "reason": "local_only"}


def _query_claude_auth_status() -> dict[str, Any]:
    """Return a small, redacted view of ``claude auth status``."""

    binary = claude_binary_path()
    if binary is None:
        return {
            "checked": False,
            "logged_in": None,
            "requires_login": False,
            "reason": "claude_not_found",
        }
    try:
        result = subprocess.run(
            [binary, "auth", "status"],
            check=False,
            capture_output=True,
            text=True, encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            timeout=CLAUDE_AUTH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {
            "checked": False,
            "logged_in": None,
            "requires_login": False,
            "reason": "auth_status_timeout",
        }
    except OSError:
        return {
            "checked": False,
            "logged_in": None,
            "requires_login": False,
            "reason": "auth_status_unavailable",
        }

    try:
        value = json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError):
        return {
            "checked": False,
            "logged_in": None,
            "requires_login": False,
            "reason": "auth_status_invalid",
        }
    if not isinstance(value, dict) or not isinstance(value.get("loggedIn"), bool):
        return {
            "checked": False,
            "logged_in": None,
            "requires_login": False,
            "reason": "auth_status_invalid",
        }

    logged_in = value["loggedIn"]
    status: dict[str, Any] = {
        "checked": True,
        "logged_in": logged_in,
        "requires_login": not logged_in,
    }
    for source, target in (
        ("authMethod", "auth_method"),
        ("subscriptionType", "subscription_type"),
        ("apiProvider", "api_provider"),
    ):
        item = value.get(source)
        if isinstance(item, str) and item.strip():
            status[target] = item.strip()
    return status


def claude_login_indicator(
    auth_status: dict[str, Any],
    *,
    rate_available: bool,
    rate_stale: bool | None,
) -> str | None:
    """Choose a login chip only when the auth check is authoritative."""

    if auth_status.get("checked") is not True:
        return None
    if auth_status.get("logged_in") is True:
        return "logged_in"
    if auth_status.get("logged_in") is False and (rate_stale is True or not rate_available):
        return "requires_login"
    return None


def add_login_indicator(rate: dict[str, Any]) -> dict[str, Any]:
    auth_status = rate.get("auth_status")
    if isinstance(auth_status, dict):
        auth_status["indicator"] = claude_login_indicator(
            auth_status,
            rate_available=rate.get("available") is True,
            rate_stale=rate.get("stale") if isinstance(rate.get("stale"), bool) else None,
        )
    return rate


def normalise_window(value: Any, now_epoch: float) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    used = finite_number(value.get("used_percentage"))
    resets_at = finite_number(value.get("resets_at"))
    if used is None and resets_at is None:
        return None
    out: dict[str, Any] = {}
    if used is not None:
        used = max(0.0, min(100.0, used))
        out["used_percentage"] = used
        out["remaining_percentage"] = 100.0 - used
    if resets_at is not None:
        out["resets_at"] = int(resets_at)
        out["reset_after_seconds"] = max(0, int(resets_at - now_epoch))
        out["resets_at_local"] = local_timestamp_text(resets_at)
    return out


def collect_rate_limits(claude_home: Path, snapshot_path: Path) -> dict[str, Any]:
    installed = statusline_is_installed(claude_home)
    base: dict[str, Any] = {
        "available": False,
        "auth_status": claude_auth_status(),
        "capture_installed": installed,
        "capture_ready": installed,
        "capture_method": "statusline" if installed else None,
        "snapshot_path": str(snapshot_path),
        "install_command": statusline_install_command(),
        "stale_after_seconds": stale_seconds(),
    }
    if not snapshot_path.exists():
        base["reason"] = "snapshot_not_found"
        return add_login_indicator(base)
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        base["reason"] = "snapshot_invalid"
        base["error"] = f"{type(exc).__name__}: {exc}"
        return add_login_indicator(base)
    if not isinstance(snapshot, dict):
        base["reason"] = "snapshot_invalid"
        return add_login_indicator(base)

    now_epoch = datetime.now(timezone.utc).timestamp()
    captured_epoch = finite_number(snapshot.get("captured_at_epoch"))
    if captured_epoch is None:
        parsed = parse_timestamp(snapshot.get("captured_at"))
        captured_epoch = parsed.timestamp() if parsed is not None else None
    age = max(0, int(now_epoch - captured_epoch)) if captured_epoch is not None else None
    rate_limits = snapshot.get("rate_limits")
    rate_limits = rate_limits if isinstance(rate_limits, dict) else {}
    source = str(snapshot.get("source") or "")
    if source == "claude_code_usage_command":
        base["capture_ready"] = True
        base["capture_method"] = "usage_command"
    elif source == "claude_code_statusline":
        base["capture_method"] = "statusline"
    five_hour = normalise_window(rate_limits.get("five_hour"), now_epoch)
    seven_day = normalise_window(rate_limits.get("seven_day"), now_epoch)

    base.update(
        {
            "available": bool(five_hour or seven_day),
            "captured_at": snapshot.get("captured_at"),
            "captured_at_unix_ms": int(captured_epoch * 1000) if captured_epoch is not None else None,
            "captured_at_local": local_timestamp_text(snapshot.get("captured_at")),
            "age_seconds": age,
            "stale": age is None or age > base["stale_after_seconds"],
            "claude_version": snapshot.get("claude_version"),
            "model": snapshot.get("model") if isinstance(snapshot.get("model"), dict) else {},
            "five_hour": five_hour,
            "seven_day": seven_day,
        }
    )
    plan_value = snapshot.get("plan_type") or snapshot.get("plan")
    if not plan_value:
        plan_value = rate_limits.get("plan_type") or rate_limits.get("plan")
    if isinstance(plan_value, str) and plan_value.strip():
        base["plan_type"] = plan_value.strip()
    limit_reached = snapshot.get("limit_reached")
    if not isinstance(limit_reached, bool):
        limit_reached = rate_limits.get("limit_reached")
    if isinstance(limit_reached, bool):
        base["limit_reached"] = limit_reached
    if not base["available"]:
        base["reason"] = "rate_limits_missing"
    return add_login_indicator(base)


def collect_usage(
    claude_home: Path | None = None,
    top_n: int = 10,
    days: int = 30,
    snapshot_path: Path | None = None,
    *, range_name: str = "all", anchor=None,
) -> dict[str, Any]:
    home = (claude_home or CLAUDE_HOME).expanduser()
    snapshot = (snapshot_path or resolve_snapshot_path(home)).expanduser()
    return {
        "ok": True,
        "retrieved_at_local": local_now_text(),
        "claude_home": str(home),
        "network_calls_made": 0,
        "privacy_note": "Usage metadata only; prompts, responses, tool inputs, and transcript content are ignored.",
        "rate_limits": collect_rate_limits(home, snapshot),
        "local_usage": aggregate_local_usage(home, top_n=max(1, top_n), days=max(1, days), range_name=range_name, anchor=anchor),
    }


def print_human(data: dict[str, Any]) -> None:
    rate = data["rate_limits"]
    local = data["local_usage"]
    totals = local["token_totals"]
    print("Claude Code Usage")
    print("=================")
    print(f"Retrieved: {data['retrieved_at_local']}")
    print(f"Claude home: {data['claude_home']}")
    print(f"Session files: {local['session_files']:,}")
    print(f"Unique requests: {local['unique_usage_records']:,}")
    print(f"Duplicate usage rows skipped: {local['duplicate_usage_records_skipped']:,}")
    print(f"Total tokens: {totals[TOTAL_FIELD]:,}")
    for label, key in (("5-hour", "five_hour"), ("7-day", "seven_day")):
        window = rate.get(key)
        if isinstance(window, dict) and window.get("used_percentage") is not None:
            print(
                f"{label} limit: {window['used_percentage']:.1f}% used, "
                f"{window['remaining_percentage']:.1f}% remaining"
            )
        else:
            print(f"{label} limit: unavailable")
    if not rate.get("capture_installed"):
        print(f"Install rate-limit capture: {rate['install_command']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read local Claude Code token and rate-limit usage.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a short summary.")
    parser.add_argument("--top", type=int, default=10, help="Number of ranked rows to return.")
    parser.add_argument("--days", type=int, default=30, help="Number of daily rows to return.")
    parser.add_argument("--claude-home", type=Path, default=CLAUDE_HOME)
    parser.add_argument("--snapshot", type=Path, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    data = collect_usage(
        claude_home=args.claude_home,
        top_n=max(1, args.top),
        days=max(1, args.days),
        snapshot_path=args.snapshot,
    )
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_human(data)


if __name__ == "__main__":
    main()
