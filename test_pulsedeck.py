from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from pulsedeck import codex_rpc
from pulsedeck.runtime import InstanceLock, Runtime, local_request, read_session, session_path

class AccountMappingTest(unittest.TestCase):
    def test_zero_and_unknown_quota_remain_distinct_and_identity_is_not_exposed(self):
        snapshot = {"limits": {"rateLimits": {
            "limitId": "codex", "planType": "test", "email": "private@example.invalid",
            "primary": {"usedPercent": 0, "resetsAt": time.time() + 120, "windowDurationMins": 300}}},
            "usage": {"summary": {"lifetimeTokens": 42}, "secret": "do-not-display"}}
        report = codex_rpc.online_report(snapshot)
        rate = report["endpoints"]["rate_limit_status"]["data"]["rate_limit"]
        self.assertEqual(rate["primary_window"]["used_percent"], 0)
        self.assertEqual(rate["primary_window"]["limit_window_seconds"], 18000)
        self.assertIsNone(rate["secondary_window"])
        self.assertFalse(rate["limit_reached"])
        self.assertNotIn("private@", json.dumps(report))
        self.assertNotIn("do-not-display", json.dumps(report))
        empty = codex_rpc.online_report({"limits": {}, "usage": {}})
        self.assertIsNone(empty["endpoints"]["rate_limit_status"]["data"]["rate_limit"]["limit_reached"])

    def test_another_metered_bucket_is_not_mislabeled(self):
        result = codex_rpc.online_report({"limits": {"rateLimits": {
            "limitId": "other", "primary": {"usedPercent": 50}}}})
        self.assertIsNone(result["endpoints"]["rate_limit_status"]["data"]["rate_limit"]["primary_window"])

    def test_reset_count_is_authoritative_and_identity_is_omitted(self):
        report = codex_rpc.resets_report({"limits": {"rateLimitResetCredits": {
            "availableCount": 3, "credits": [{"id": "private-credit-id", "status": "available",
            "resetType": "codexRateLimits", "grantedAt": 1781654400, "expiresAt": None}]}}})
        self.assertEqual(report["available_count"], 3)
        self.assertEqual(report["credits_returned"], 1)
        self.assertTrue(report["details_available"])
        self.assertNotIn("private-credit-id", json.dumps(report))
        self.assertIsNone(codex_rpc.resets_report({"limits": {}}))
        count_only=codex_rpc.resets_report({"limits":{"rateLimitResetCredits":{"availableCount":3,"credits":None}}})
        self.assertEqual(count_only["available_count"],3)
        self.assertFalse(count_only["details_available"])
        self.assertIsNone(count_only["credits_returned"])
        empty=codex_rpc.resets_report({"limits":{"rateLimitResetCredits":{"availableCount":0,"credits":[]}}})
        self.assertEqual(empty["available_count"],0)
        self.assertTrue(empty["details_available"])

class RuntimeTest(unittest.TestCase):
    def test_single_instance_lock_releases_after_failure(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"PULSEDECK_DATA_DIR": directory}):
            with InstanceLock():
                with self.assertRaises(RuntimeError):
                    with InstanceLock():
                        pass
            with InstanceLock():
                pass

    def test_invalid_state_is_not_used_for_control_requests(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"PULSEDECK_DATA_DIR": directory}):
            session_path().write_text('{"root":"another-project","port":8765,"token":"x"}', encoding="utf-8")
            self.assertIsNone(read_session())
            session_path().write_text('not json', encoding="utf-8")
            self.assertIsNone(read_session())

    def test_control_requires_authentication_and_explicit_stop_action(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"PULSEDECK_DATA_DIR": directory}):
            runtime = Runtime(port=0, sources="codex")
            thread = threading.Thread(target=runtime.serve, daemon=True)
            thread.start()
            try:
                deadline = time.monotonic() + 3
                while not session_path().exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                session = runtime.session
                self.assertEqual(local_request(session, "/api/pulsedeck")["application"], "PulseDeck")
                with self.assertRaises(urllib.error.HTTPError) as error:
                    local_request({**session, "token": "wrong"}, "/api/pulsedeck")
                self.assertEqual(error.exception.code, 403)
                request = urllib.request.Request(
                    f"http://127.0.0.1:{session['port']}/api/pulsedeck/stop",
                    headers={"Authorization": "Bearer " + session["token"]}, method="POST")
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(request, timeout=2)
                self.assertEqual(error.exception.code, 403)
                self.assertTrue(local_request(session, "/api/pulsedeck/stop", stop=True)["ok"])
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                self.assertFalse(session_path().exists())
            finally:
                if thread.is_alive():
                    runtime.server.shutdown()
                    thread.join(timeout=5)

if __name__ == "__main__":
    unittest.main()
