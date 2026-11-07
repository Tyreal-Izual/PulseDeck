"""Real loopback collisions, default-port fallback, and exclusive ownership."""
import errno
from http.server import BaseHTTPRequestHandler
import os
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import codex_claude_usage_web as web
from pulsedeck.desktop import DesktopBackend
from pulsedeck.runtime import Runtime, local_request, port_unavailable


def listener(reuse=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if reuse:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return sock
    except BaseException:
        sock.close()
        raise


class PortBindingTest(unittest.TestCase):
    def test_server_cannot_share_an_existing_listener(self):
        for reuse in (False, True):
            with self.subTest(owner_reuses_address=reuse), listener(reuse) as owner:
                server = None
                try:
                    with self.assertRaises(OSError):
                        server = web.BoundedThreadingHTTPServer(owner.getsockname(), BaseHTTPRequestHandler, max_workers=1)
                finally:
                    if server is not None:
                        server.server_close()

    def test_other_listeners_cannot_take_over_our_address(self):
        server = web.BoundedThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler, max_workers=1)
        try:
            if sys.platform == "win32":
                self.assertEqual(server.socket.getsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR), 0)
                self.assertEqual(server.socket.getsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE), 1)
            modes = [(), (socket.SO_REUSEADDR,)]
            if hasattr(socket, "SO_REUSEPORT"):
                modes.append((socket.SO_REUSEADDR, socket.SO_REUSEPORT))
            for options in modes:
                with self.subTest(options=options), socket.socket() as rival:
                    for option in options:
                        rival.setsockopt(socket.SOL_SOCKET, option, 1)
                    with self.assertRaises(OSError):
                        rival.bind(server.server_address)
                        rival.listen(1)
        finally:
            server.server_close()

    def test_both_default_entrypoints_recover_from_real_bind_conflicts(self):
        # Redirect only the requested default to a held ephemeral port. The bind,
        # OSError, fallback bind and authenticated HTTP request all remain real,
        # without interfering with an installed app already using 8765/8766.
        real_create = web.create_server
        for desktop, default in ((False, 8765), (True, 8766)):
            for reuse in (False, True):
                with self.subTest(desktop=desktop, owner_reuses_address=reuse), tempfile.TemporaryDirectory() as directory, \
                     patch.dict(os.environ, {"PULSEDECK_DATA_DIR": directory}), listener(reuse) as owner:
                    occupied = owner.getsockname()[1]
                    attempts = []
                    def create(host, port, **options):
                        attempts.append(port)
                        return real_create(host, occupied if port == default else port, **options)
                    backend = runtime = worker = None
                    try:
                        with patch.object(web, "create_server", side_effect=create):
                            if desktop:
                                backend = DesktopBackend(sources="codex")
                                runtime = backend.runtime
                            else:
                                runtime = Runtime(sources="codex")
                        self.assertEqual(attempts, [default, 0])
                        self.assertNotEqual(runtime.session["port"], occupied)
                        if backend:
                            backend.start()
                        else:
                            worker = threading.Thread(target=runtime.serve, daemon=True)
                            worker.start()
                            self.assertTrue(runtime.ready.wait(3))
                        info = local_request(runtime.session, "/api/pulsedeck")
                        self.assertEqual(info["application"], "PulseDeck")
                        self.assertEqual(info["presentation"], "desktop" if desktop else "browser")
                    finally:
                        if backend:
                            backend.close()
                        elif worker and worker.is_alive():
                            runtime.server.shutdown()
                            worker.join(3)
                        elif runtime:
                            runtime.server.server_close()
                    self.assertFalse(runtime.state_path.exists())

    def test_fixed_nondefault_ports_and_unrelated_errors_are_not_hidden(self):
        for factory in (Runtime, DesktopBackend):
            with self.subTest(factory=factory.__name__), listener() as owner:
                with self.assertRaises(OSError):
                    factory(port=owner.getsockname()[1], sources="codex")
            with patch.object(web, "create_server", side_effect=OSError(errno.EINVAL, "bad bind")) as create:
                with self.assertRaises(OSError):
                    factory(sources="codex")
                self.assertEqual(create.call_count, 1)

    def test_windows_access_denied_is_a_fallback_condition_only_on_windows(self):
        denied = OSError(errno.EACCES, "access denied")
        winsock_only = OSError("bind denied")
        winsock_only.winerror = 10013
        with patch("pulsedeck.runtime.sys.platform", "win32"):
            for error in (denied, winsock_only, OSError(10013, "denied"), OSError(10048, "in use")):
                self.assertTrue(port_unavailable(error))
            self.assertFalse(port_unavailable(OSError(errno.EINVAL, "bad bind")))
        with patch("pulsedeck.runtime.sys.platform", "linux"):
            self.assertFalse(port_unavailable(denied))
            self.assertFalse(port_unavailable(winsock_only))
        self.assertTrue(port_unavailable(OSError(errno.EADDRINUSE, "in use")))


if __name__ == "__main__":
    unittest.main()
