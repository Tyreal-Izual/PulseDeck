"""Local application lifecycle, independent of the browser launcher."""
from __future__ import annotations

import errno
import json
import os
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import __version__
from .modules import describe
from usage_common import atomic_write_json, cache_directory
from usage_sources import resolve_sources

ROOT = Path(__file__).resolve().parent.parent

def port_unavailable(error: OSError) -> bool:
    """Bind conflicts, including Windows exclusive/excluded-port access errors."""
    if error.errno == errno.EADDRINUSE:
        return True
    return sys.platform == "win32" and (
        error.errno in {errno.EACCES, 10013, 10048}
        or getattr(error, "winerror", None) in {10013, 10048}
    )

def data_directory() -> Path:
    override = os.environ.get("PULSEDECK_DATA_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "PulseDeck"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/PulseDeck"
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "pulsedeck"

def session_path() -> Path:
    return data_directory() / "run.json"

def read_session(path: Path | None = None, *, require_root: bool = True) -> dict | None:
    try:
        value = json.loads((path or session_path()).read_text(encoding="utf-8"))
        if not isinstance(value, dict) or (require_root and value.get("root") != str(ROOT)):
            return None
        port = value.get("port")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            return None
        if not isinstance(value.get("token"), str) or not value["token"]:
            return None
        return value
    except (OSError, ValueError):
        return None

def local_request(session: dict, path: str, *, stop: bool = False, action: str | None = None) -> dict:
    # Never use a URL read from disk: control requests are always loopback-only.
    request = urllib.request.Request(
        f"http://127.0.0.1:{session['port']}{path}",
        headers={"Authorization": "Bearer " + session["token"],
                 "X-PulseDeck-Action": action or ("stop" if stop else "read")},
        method="POST" if stop or action else "GET",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=2) as response:
        return json.load(response)

def running_session() -> dict | None:
    session = read_session()
    if session:
        try:
            result = local_request(session, "/api/pulsedeck")
            if result.get("application") == "PulseDeck":
                return session
        except (OSError, ValueError, urllib.error.URLError):
            pass
    return None

def access_url(session: dict) -> str:
    return f"http://127.0.0.1:{session['port']}/?" + urllib.parse.urlencode(
        {"access_token": session["token"]})

class InstanceLock:
    """OS lock released automatically if the process crashes."""
    def __init__(self, path: Path | None = None):
        self.path = path

    def __enter__(self):
        path = self.path or data_directory() / "instance.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = path.open("a+b")
        self.handle.seek(0, 2)
        if self.handle.tell() == 0:
            self.handle.write(b"0")
            self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.handle.close()
            raise RuntimeError("PulseDeck is already starting or running.")
        return self

    def __exit__(self, *args):
        self.handle.close()

class Runtime:
    """Owns local collectors and authenticated transport for either presentation."""
    def __init__(self, *, port: int = 8765, sources: str = "auto",
                 state_path: Path | None = None, presentation: str = "browser", on_activate=None,
                 on_stop=None):
        import codex_claude_usage_web as web
        import codex_usage

        class Handler(web.UsageWebHandler):
            def do_GET(handler):
                if urllib.parse.urlparse(handler.path).path != "/api/pulsedeck":
                    return super().do_GET()
                if handler.reject_untrusted_host(include_body=True) or handler.reject_missing_access(include_body=True):
                    return
                with handler.server.sources_lock:
                    enabled = handler.server.enabled_sources
                handler.send_json({"application": "PulseDeck", "version": __version__, "presentation": presentation,
                                   "modules": describe(enabled)})

            def do_POST(handler):
                if urllib.parse.urlparse(handler.path).path == "/api/pulsedeck/activate":
                    if handler.reject_untrusted_host(include_body=True) or handler.reject_missing_access(include_body=True):
                        return
                    if handler.headers.get("X-PulseDeck-Action") != "activate":
                        handler.send_json({"ok": False, "error": "activate action required"}, status=403)
                        return
                    if on_activate is None:
                        handler.send_json({"ok": False, "error": "no desktop window"}, status=404)
                        return
                    on_activate()
                    handler.send_json({"ok": True})
                    return
                if urllib.parse.urlparse(handler.path).path != "/api/pulsedeck/stop":
                    return super().do_POST()
                if handler.reject_untrusted_host(include_body=True) or handler.reject_missing_access(include_body=True):
                    return
                if handler.headers.get("X-PulseDeck-Action") != "stop":
                    handler.send_json({"ok": False, "error": "stop action required"}, status=403)
                    return
                handler.send_json({"ok": True})
                threading.Thread(target=on_stop or handler.server.shutdown, daemon=True).start()

        token = secrets.token_urlsafe(32)
        options = dict(access_token=token, allowed_hosts=[], max_workers=8,
                       max_collectors=4, cache_seconds=5,
                       enabled_sources=resolve_sources(sources, codex_usage.CODEX_HOME),
                       cache_dir=cache_directory())
        try:
            self.server = web.create_server("127.0.0.1", port, **options)
        except OSError as exc:
            # A busy default port should not prevent a local app from starting.
            if port != 8765 or not port_unavailable(exc):
                raise
            self.server = web.create_server("127.0.0.1", 0, **options)
        self.server.RequestHandlerClass = Handler
        self.server.local_days = 30
        self.server.refresh_seconds = 15
        self.server.quiet = True
        self.session = {"root": str(ROOT), "port": self.server.server_address[1],
                        "pid": os.getpid(), "token": token, "started_at": time.time()}
        self.state_path = state_path or session_path()
        self.ready = threading.Event()

    def serve(self):
        try:
            atomic_write_json(self.state_path, self.session)
            self.server.radar_service.start()
            self.ready.set()
            self.server.serve_forever(poll_interval=0.2)
        finally:
            self.server.server_close()
            current = read_session(self.state_path, require_root=False)
            if current and current.get("token") == self.session["token"]:
                self.state_path.unlink(missing_ok=True)
