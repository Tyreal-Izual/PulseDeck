import argparse
import unittest
from unittest.mock import patch
import codex_usage
import claude_usage
from pulsedeck import codex_rpc
from usage_common import CollectionError

class LocalOnlyTest(unittest.TestCase):
    def test_account_collection_never_reads_credentials_or_launches_clients(self):
        with patch.object(codex_usage, "load_auth", side_effect=AssertionError("credentials")), patch.object(codex_rpc.subprocess, "Popen", side_effect=AssertionError("process")), patch("subprocess.run", side_effect=AssertionError("client")):
            self.assertTrue(codex_usage.collect_online_usage()["local_only"])
            self.assertTrue(codex_usage.collect_resets()["local_only"])
            self.assertTrue(codex_usage.collect_api_usage(argparse.Namespace())["local_only"])
            self.assertIsNone(codex_rpc.account_snapshot())
            self.assertIsNone(codex_usage.admin_api_key())
            self.assertEqual(claude_usage.claude_auth_status()["reason"], "local_only")

    def test_low_level_account_transports_are_disabled(self):
        with self.assertRaises(CollectionError):
            codex_usage.fetch_json("/wham/usage", "dummy", "dummy")
        with self.assertRaises(CollectionError):
            codex_usage.fetch_admin_json("/usage", {}, "dummy")
        with self.assertRaises(RuntimeError):
            codex_rpc.read_account(None)
