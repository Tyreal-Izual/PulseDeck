import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
from unittest.mock import patch

from pulsedeck.desktop import DesktopBackend, activate_existing, desktop_directory, local_navigation
from pulsedeck.runtime import InstanceLock, local_request, read_session, session_path


class DesktopLifecycleTest(unittest.TestCase):
    def test_desktop_owns_separate_state_and_closes_its_backend(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"PULSEDECK_DATA_DIR": directory}):
            session_path().write_text('{"legacy":true}', encoding="utf-8")
            activated = threading.Event()
            backend = DesktopBackend(sources="codex", port=0, on_activate=activated.set)
            try:
                url = backend.start()
                self.assertIn("127.0.0.1", url)
                state = read_session(desktop_directory() / "run.json", require_root=False)
                self.assertIsNotNone(state)
                self.assertTrue(activate_existing())
                self.assertTrue(activated.is_set())
                with self.assertRaises(urllib.error.HTTPError) as error:
                    local_request({**state, "token": "wrong"}, "/api/pulsedeck/activate", action="activate")
                self.assertEqual(error.exception.code, 403)
                with self.assertRaises(urllib.error.HTTPError) as error:
                    local_request(state, "/api/pulsedeck/activate", action="wrong")
                self.assertEqual(error.exception.code, 403)
            finally:
                backend.close()
            self.assertFalse(backend.thread.is_alive())
            self.assertFalse((desktop_directory() / "run.json").exists())
            self.assertEqual(json.loads(session_path().read_text()), {"legacy": True})

    def test_desktop_lock_does_not_share_legacy_lock(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"PULSEDECK_DATA_DIR": directory}):
            path = desktop_directory() / "instance.lock"
            with InstanceLock(), InstanceLock(path):
                with self.assertRaises(RuntimeError):
                    with InstanceLock(path):
                        pass

    def test_stop_request_is_delivered_to_desktop_owner(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"PULSEDECK_DATA_DIR": directory}):
            closed = threading.Event()
            backend = DesktopBackend(sources="codex", port=0, on_stop=closed.set)
            try:
                backend.start()
                self.assertTrue(local_request(backend.runtime.session, "/api/pulsedeck/stop", stop=True)["ok"])
                self.assertTrue(closed.wait(2))
                self.assertTrue(backend.thread.is_alive())
            finally:
                backend.close()
            self.assertFalse((desktop_directory() / "run.json").exists())

    def test_navigation_stays_on_authenticated_local_origin(self):
        self.assertTrue(local_navigation("http://127.0.0.1:8766/?report=all", 8766))
        self.assertTrue(local_navigation("about:blank", 8766))
        for url in ("http://127.0.0.1:8767/", "https://127.0.0.1:8766/", "file:///C:/secret",
                    "https://example.com", "http://user@127.0.0.1:8766/", "http://127.0.0.1:bad/"):
            self.assertFalse(local_navigation(url, 8766), url)


if __name__ == "__main__":
    unittest.main()
