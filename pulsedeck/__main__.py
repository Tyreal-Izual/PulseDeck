"""python -m pulsedeck: launch, serve, stop, check."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from .runtime import (ROOT, InstanceLock, Runtime, access_url, data_directory,
                      local_request, running_session)

def launch(*, browser: bool = True, port: int = 8765, sources: str = "auto") -> int:
    session = running_session()
    if not session:
        logs = data_directory() / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        flags = (subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS) if os.name == "nt" else 0
        env = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        with (logs / "server.log").open("a", encoding="utf-8") as log:
            process = subprocess.Popen(
                [sys.executable, "-X", "utf8", "-B", "-m", "pulsedeck",
                 "serve", "--port", str(port), "--sources", sources],
                cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                creationflags=flags, start_new_session=os.name != "nt",
            )
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            session = running_session()
            if session:
                break
            if process.poll() is not None:
                break
            time.sleep(0.2)
        if not session:
            print(f"PulseDeck did not start. See {logs / 'server.log'}", file=sys.stderr)
            return 1
    if browser:
        webbrowser.open(access_url(session))
    print(f"PulseDeck is running on 127.0.0.1:{session['port']}.")
    return 0

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="PulseDeck local monitoring dashboard")
    parser.add_argument("command", nargs="?", default="launch",
                        choices=("launch", "serve", "stop", "check", "capture-claude"))
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--sources", default="auto")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("--port must be between 0 and 65535")
    if args.command == "check":
        from codex_claude_usage_web import main as check
        check(["--check", "--sources", args.sources])
        return 0
    if args.command == "capture-claude":
        from claude_usage_statusline import install
        install(False)
        return 0
    if args.command == "stop":
        session = running_session()
        if not session:
            print("PulseDeck is not running.")
            return 0
        local_request(session, "/api/pulsedeck/stop", stop=True)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and running_session():
            time.sleep(0.2)
        if running_session():
            print("PulseDeck is still stopping.", file=sys.stderr)
            return 1
        print("PulseDeck stopped.")
        return 0
    if args.command == "launch":
        return launch(browser=not args.no_browser, port=args.port, sources=args.sources)
    try:
        with InstanceLock():
            Runtime(port=args.port, sources=args.sources).serve()
    except KeyboardInterrupt:
        pass
    except (RuntimeError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
