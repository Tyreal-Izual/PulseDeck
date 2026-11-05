import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import codex_usage
import claude_usage
from pulsedeck.local_quota import codex_snapshot, quota_report
from pulsedeck.local_usage import CODEX_INDEX


class LocalQuotaTest(unittest.TestCase):
    captured = datetime(2026, 11, 5, 12, tzinfo=timezone.utc)

    def test_weekly_only_primary_is_not_mislabeled_as_five_hour(self):
        snapshot = codex_snapshot({"limit_id":"codex", "primary":{
            "window_minutes":10080, "used_percent":31, "resets_at":1794432162}}, self.captured)
        self.assertIsNone(snapshot["five_hour"])
        self.assertEqual(snapshot["seven_day"]["remaining_percentage"], 69)

    def test_both_windows_and_unknown_are_distinct_from_zero_usage(self):
        snapshot = codex_snapshot({"primary":{"window_minutes":300, "used_percent":0},
                                   "secondary":{"window_minutes":10080, "used_percent":100}}, self.captured)
        self.assertEqual(snapshot["five_hour"]["remaining_percentage"], 100)
        self.assertEqual(snapshot["seven_day"]["remaining_percentage"], 0)
        empty = codex_snapshot({"primary":{"window_minutes":300}}, self.captured)
        self.assertIsNone(empty["five_hour"])
        self.assertFalse(quota_report(empty)["available"])

    def test_other_buckets_identity_and_invalid_fields_are_not_retained(self):
        self.assertIsNone(codex_snapshot({"limit_id":"other"}, self.captured))
        result = codex_snapshot({"limit_id":"codex", "email":"PRIVATE_SENTINEL",
            "credits":{"id":"PRIVATE_SENTINEL"}, "primary":{"window_minutes":300,
            "used_percent":float("nan"), "resets_at":10**1000}}, self.captured)
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))
        self.assertIsNone(result["five_hour"])

    def test_age_and_countdown_recompute_without_mutating_the_snapshot(self):
        now = self.captured.timestamp()
        snapshot = codex_snapshot({"primary":{"window_minutes":300, "used_percent":20,
                                   "resets_at":now+100}}, self.captured)
        first, later = quota_report(snapshot, now), quota_report(snapshot, now+901)
        self.assertFalse(first["stale"])
        self.assertTrue(later["stale"])
        self.assertEqual(later["five_hour"]["reset_after_seconds"], 0)
        self.assertNotIn("reset_after_seconds", snapshot["five_hour"])
        self.assertFalse(quota_report(None)["available"])

    def test_quota_is_incremental_and_independent_of_history_range(self):
        CODEX_INDEX.entries.clear()
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory).resolve()
            path=home/'sessions'/'usage.jsonl'
            path.parent.mkdir()
            def row(percent, when):
                return json.dumps({"type":"event_msg", "timestamp":when, "payload":{
                    "type":"token_count", "info":None, "rate_limits":{"limit_id":"codex",
                    "primary":{"window_minutes":10080,"used_percent":percent}}}})+'\n'
            path.write_text(row(20,"2026-11-04T12:00:00Z"),encoding='utf-8')
            with patch.object(codex_usage, 'load_auth', side_effect=AssertionError('credentials')), patch('socket.socket',side_effect=AssertionError('network')):
                first=codex_usage.collect_local_usage(home,10,'today','2026-11-05')
                cached=codex_usage.collect_local_usage(home,10,'7d','2026-11-05')
                self.assertEqual(first['rate_limits']['seven_day']['remaining_percentage'],80)
                self.assertEqual(cached['usage']['refresh']['bytes_read'],0)
                self.assertEqual(first['usage']['token_totals']['total_tokens'],0)
                with path.open('a',encoding='utf-8') as f:
                    f.write(row(31,"2026-11-05T12:00:00Z"))
                updated=codex_usage.collect_local_usage(home,10,'all','2026-11-05')
                self.assertEqual(updated['rate_limits']['seven_day']['remaining_percentage'],69)
                self.assertEqual(updated['usage']['refresh']['files_appended'],1)

    def test_claude_snapshot_timestamp_supports_epoch_and_iso_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory)
            path=home/'quota.json'
            for captured in ({'captured_at':self.captured.isoformat()}, {'captured_at_epoch':self.captured.timestamp()}):
                path.write_text(json.dumps({**captured,'rate_limits':{
                    'five_hour':{'used_percentage':25,'resets_at':self.captured.timestamp()+3600},
                    'seven_day':{'used_percentage':40,'resets_at':self.captured.timestamp()+86400}}}),encoding='utf-8')
                with patch('socket.socket',side_effect=AssertionError('network')), patch('subprocess.run',side_effect=AssertionError('client')):
                    result=claude_usage.collect_rate_limits(home,path)
                self.assertEqual(result['captured_at_unix_ms'],int(self.captured.timestamp()*1000))
                self.assertEqual(result['five_hour']['remaining_percentage'],75)
                self.assertEqual(result['seven_day']['remaining_percentage'],60)


@unittest.skipUnless(shutil.which('node'), 'Node.js is needed for quota rendering tests')
class QuotaRendererTest(unittest.TestCase):
    def test_countdown_ticks_and_expired_or_missing_quota_never_becomes_full(self):
        root=Path(__file__).parent
        script='''
        const TEXT={en:{resetsIn:'Resets in',day:'day',left:'left'},zh:{}},state={lang:'en'};
        const t=k=>TEXT.en[k]||k,esc=v=>String(v??''),asNumber=v=>Number.isFinite(Number(v))?Number(v):null;
        const trackedNumber=(key,value,display)=>display??value;
        Date.now=()=>1000000;
        '''+(root/'static/usage.js').read_text(encoding='utf-8')+'''
        const current=quotaBar('codex','five_hour',{used_percentage:30,resets_at:1005},'5h');
        const expired=quotaBar('codex','five_hour',{used_percentage:30,resets_at:999},'5h');
        const unknown=quotaBar('claude','five_hour',null,'5h');
        console.log(JSON.stringify({current,expired,unknown,start:quotaCountdown(1005),later:quotaCountdown(1005,1003000)}));
        '''
        result=subprocess.run([shutil.which('node')],input=script,text=True,encoding='utf-8',capture_output=True,timeout=5,check=True)
        data=json.loads(result.stdout)
        self.assertIn('70.0%',data['current'])
        self.assertNotIn('70.0%',data['expired'])
        self.assertNotIn('100.0%',data['unknown'])
        self.assertIn('00:00:05',data['start'])
        self.assertIn('00:00:02',data['later'])


if __name__=='__main__':
    unittest.main()
