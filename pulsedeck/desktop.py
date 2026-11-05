"""Standalone Windows window. The embedded backend is owned by this process."""
from __future__ import annotations

import errno
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import urllib.parse
import webbrowser

from .runtime import (InstanceLock, Runtime, access_url, data_directory,
                      local_request, read_session)

LOGGER = logging.getLogger("pulsedeck.desktop")


def desktop_directory() -> Path:
    return data_directory() / "desktop"


def running_desktop_session() -> dict | None:
    # One-file packages unpack to a different temporary root on every start.
    session = read_session(desktop_directory() / "run.json", require_root=False)
    if not session:
        return None
    try:
        info = local_request(session, "/api/pulsedeck")
        if info.get("application") != "PulseDeck" or info.get("presentation") != "desktop":
            return None
        return session
    except (OSError, ValueError):
        return None


def activate_existing() -> bool:
    session = running_desktop_session()
    if session is None:
        return False
    try:
        return bool(local_request(session, "/api/pulsedeck/activate", action="activate").get("ok"))
    except (OSError, ValueError):
        return False


class DesktopBackend:
    def __init__(self, *, sources: str = "auto", port: int = 8766, on_activate=None, on_stop=None):
        options = dict(sources=sources, state_path=desktop_directory() / "run.json",
                       presentation="desktop", on_activate=on_activate, on_stop=on_stop)
        try:
            self.runtime = Runtime(port=port, **options)
        except OSError as error:
            if port != 8766 or error.errno not in {errno.EADDRINUSE, 10048}:
                raise
            self.runtime = Runtime(port=0, **options)
        self.error = None
        self.thread = threading.Thread(target=self._serve, name="PulseDeck-local", daemon=True)

    def _serve(self):
        try:
            self.runtime.serve()
        except Exception as error:
            self.error = error
            LOGGER.exception("Desktop backend stopped")
        finally:
            self.runtime.ready.set()

    def start(self):
        self.thread.start()
        if not self.runtime.ready.wait(5):
            raise RuntimeError("本地采集模块启动超时。")
        if self.error:
            raise RuntimeError("本地采集模块未能启动。") from self.error
        return access_url(self.runtime.session)

    def close(self):
        if self.thread.is_alive():
            self.runtime.server.shutdown()
            self.thread.join(timeout=4)
        else:
            self.runtime.server.server_close()


def local_navigation(url: str, port: int) -> bool:
    if url == "about:blank":
        return True
    try:
        parsed = urllib.parse.urlsplit(url)
        return (parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
                and parsed.port == port and parsed.username is None and parsed.password is None)
    except ValueError:
        return False


def attach_navigation_policy(window, port: int):
    """Keep the embedded window on our own origin; external links need a user click."""
    def navigation_start(_sender, event):
        url = str(event.Uri)
        if local_navigation(url, port):
            return
        event.Cancel = True
        parsed = urllib.parse.urlsplit(url)
        if event.IsUserInitiated and parsed.scheme in {"https", "http"}:
            webbrowser.open(url)

    window.native.browser.webview.NavigationStarting += navigation_start
    # Keep the delegate alive for the lifetime of the native event subscription.
    window._pulsedeck_navigation = navigation_start


def run() -> int:
    if sys.platform != "win32":
        raise RuntimeError("此桌面版面向 Windows；其他系统可继续使用本地浏览器入口。")
    lock = InstanceLock(desktop_directory() / "instance.lock")
    try:
        lock.__enter__()
    except RuntimeError:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if activate_existing():
                return 0
            time.sleep(0.2)
        raise RuntimeError("PulseDeck 已在启动或运行，请稍后再试。")

    backend = None
    try:
        import webview

        window = None

        def activate():
            if window is not None and window.events.shown.is_set():
                def focus():
                    try:
                        # show() activates the native window; restore a minimized one.
                        from System import Action
                        from System.Windows.Forms import FormWindowState

                        def native_focus():
                            if window.native.WindowState == FormWindowState.Minimized:
                                window.native.WindowState = FormWindowState.Normal
                            window.native.Show()
                            window.native.Activate()
                        window.native.BeginInvoke(Action(native_focus))
                    except Exception:
                        LOGGER.exception("Could not activate the desktop window")
                threading.Thread(target=focus, daemon=True).start()

        def close_window():
            if window is not None:
                window.destroy()

        backend = DesktopBackend(on_activate=activate, on_stop=close_window)
        url = backend.start()
        window = webview.create_window(
            "PulseDeck", url=url, width=1380, height=920, min_size=(760, 560),
            background_color="#0b1110", text_select=True, zoomable=True,
        )
        window.events.before_show += lambda: attach_navigation_policy(window, backend.runtime.session["port"])
        webview.settings["ALLOW_FILE_URLS"] = False
        webview.settings["ALLOW_DOWNLOADS"] = False
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
        webview.start(gui="edgechromium", debug=False, private_mode=False,
                      storage_path=str(desktop_directory() / "webview"))
        return 0
    finally:
        if backend is not None:
            backend.close()
        lock.__exit__(None, None, None)


def self_check(output: Path) -> int:
    """Packaged smoke check: assets, local authentication and cleanup; no account/network sources."""
    from .privacy import ACCOUNT_NETWORK_ENABLED
    import dashboard_assets
    import webview  # verifies that the package includes the desktop dependency
    import clr  # verifies the .NET bridge, without creating a window

    original = os.environ.get("PULSEDECK_DATA_DIR")
    result = {}
    try:
        with tempfile.TemporaryDirectory(prefix="pulsedeck-desktop-check-") as directory:
            os.environ["PULSEDECK_DATA_DIR"] = directory
            activated = threading.Event()
            backend = DesktopBackend(sources="codex", port=0, on_activate=activated.set)
            try:
                backend.start()
                info = local_request(backend.runtime.session, "/api/pulsedeck")
                local_request(backend.runtime.session, "/api/pulsedeck/activate", action="activate")
                result = {"ok": True, "presentation": info["presentation"],
                          "assets": "<title>PulseDeck</title>" in dashboard_assets.load_page("index"),
                          "account_network_enabled": ACCOUNT_NETWORK_ENABLED,
                          "activation": activated.is_set()}
            finally:
                backend.close()
            result["clean_shutdown"] = not (Path(directory) / "desktop/run.json").exists()
    finally:
        if original is None:
            os.environ.pop("PULSEDECK_DATA_DIR", None)
        else:
            os.environ["PULSEDECK_DATA_DIR"] = original
    result["ok"] = (result.get("assets") and result.get("activation")
                    and result.get("clean_shutdown") and not result.get("account_network_enabled"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    folder = desktop_directory()
    folder.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(folder / "desktop.log", maxBytes=1_000_000,
                                  backupCount=1, encoding="utf-8")
    logging.basicConfig(level=logging.WARNING, handlers=[handler])
    try:
        if len(args) == 2 and args[0] == "--self-check":
            return self_check(Path(args[1]).resolve())
        if args:
            return 2
        return run()
    except Exception as error:
        LOGGER.exception("Desktop startup failed")
        if not args and sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                None, "PulseDeck 未能启动。\n\n" + str(error)
                + "\n\n日志：" + str(folder / "desktop.log"), "PulseDeck", 0x10)
        return 1
    finally:
        handler.close()


if __name__ == "__main__":
    raise SystemExit(main())
