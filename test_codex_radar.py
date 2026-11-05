from __future__ import annotations

import http.client
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import codex_radar as radar
import codex_claude_usage_web as web


def legacy_snapshot(kind=None):
    # Only rejection of historical formats is maintained; their scoring code is retired.
    return {"benchmark_kind":kind, "source_updated_at":"2026-09-07T12:00:00Z",
            "points":[{"model":"gpt-6-astra", "effort":"high", "iq":120, "combined_cost_index":100}]}


def degradation_html(score=107.3):
    rows = ''.join(f'<button data-cir-setting="{model}:{effort}"><span><strong>{score}</strong>'
                   '<span data-cir-cost>999.99</span></span></button>'
                   for model, efforts in radar.DEGRADATION_EFFORTS.items() for effort in efforts)
    return ('<html><body><section id="stationmaster-round" data-intelligence-ui>'
            '<link rel="stylesheet" href="ignored.css"><p class="cir-meta">4 个分项 · 46 档 · 总分150</p>'
            '<p class="cir-test-time">本轮测试：2026-10-31 13:31–16:53（北京时间）</p>'
            '<div data-cir-panel="total"><table><caption>总分 /150 · 费用</caption><tbody><tr><td>'
            + rows + '</td></tr></tbody></table></div>'
            '<div data-cir-panel="pelican"><button data-cir-setting="gpt-6-astra:high"><strong>1</strong></button></div>'
            '<script>var ignored = 123;</script></section></body></html>')


def degradation_fixture():
    return radar.degradation_snapshot(degradation_html())


class DegradationTest(unittest.TestCase):
    def test_homepage_totals_are_read_without_regrading_or_costs(self):
        result = degradation_fixture()
        self.assertTrue(radar.validate_degradation_snapshot(result))
        self.assertEqual(len(result['points']), 46)
        self.assertEqual({p['score'] for p in result['points']}, {107.3})
        self.assertEqual(result['source_updated_at'], '2026-10-31T08:53:00+00:00')
        self.assertIn('gpt-6.1-terra', {p['model'] for p in result['points']})
        self.assertIn('gpt-5.6-terra', {p['model'] for p in result['points']})
        self.assertNotIn('999.99', json.dumps(result))
        self.assertNotIn('ignored.css', json.dumps(result))

    def test_missing_and_zero_remain_distinct(self):
        for text, expected in (('—', None), ('0', 0), ('150.00', 150)):
            with self.subTest(text=text):
                snapshot = radar.degradation_snapshot(degradation_html(text))
                self.assertTrue(radar.validate_degradation_snapshot(snapshot))
                self.assertEqual(snapshot['points'][0]['score'], expected)

    def test_progress_notice_seconds_and_unscored_configuration_are_supported(self):
        source = degradation_html().replace(
            '本轮测试：2026-10-31 13:31–16:53（北京时间）',
            '本轮测试：2026-11-04 09:24:08–11:53:41（北京时间）')
        source = source.replace('<div data-cir-panel="total">',
            '<p class="cir-meta">183/184 项已判 · 45档有总分 · 1项按要求停测</p><div data-cir-panel="total">')
        source = source.replace(
            'data-cir-setting="gpt-5.6-terra:ultra"><span><strong>107.3</strong>',
            'data-cir-setting="gpt-5.6-terra:ultra"><span><strong>—</strong>')
        snapshot = radar.degradation_snapshot(source)
        self.assertTrue(radar.validate_degradation_snapshot(snapshot))
        self.assertEqual(snapshot['source_started_at'], '2026-11-04T01:24:08+00:00')
        self.assertEqual(snapshot['source_updated_at'], '2026-11-04T03:53:41+00:00')
        self.assertEqual(len(snapshot['points']), 46)
        missing = [p for p in snapshot['points'] if p['score'] is None]
        self.assertEqual(missing, [{'model':'gpt-5.6-terra', 'effort':'ultra', 'score':None}])
        duplicate = source.replace('183/184 项已判 · 45档有总分 · 1项按要求停测', '4 个分项 · 46 档 · 总分150')
        with self.assertRaises(ValueError): radar.degradation_snapshot(duplicate)
        with self.assertRaises(ValueError):
            radar.degradation_snapshot(source.replace('11:53:41', '11:53:99'))

    def test_changed_incomplete_or_ambiguous_page_is_rejected(self):
        html = degradation_html()
        cases = [html.replace('总分150','总分100'), html.replace('4 个分项','5 个分项'),
                 html.replace('gpt-6.1-sol:medium','gpt-6.1-sol:low'),
                 html.replace('gpt-6.1-sol:low','unknown:low'),
                 html.replace('<strong>107.3</strong>', '<strong>151</strong>', 1),
                 html.replace('<strong>107.3</strong>', '<strong>NaN</strong>', 1),
                 html.replace(' data-intelligence-ui',''),
                 html.replace('13:31–16:53','16:53–13:31'), html[:-20], html+html,
                 html.replace('data-cir-panel="total"','data-cir-panel="other"')]
        for index, source in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                radar.degradation_snapshot(source)
        snapshot = degradation_fixture()
        snapshot['points'][0]['score'] = float('nan')
        self.assertFalse(radar.validate_degradation_snapshot(snapshot))
        self.assertFalse(radar.validate_degradation_snapshot(legacy_snapshot("radar-bench-v2-150")))

    def test_transport_bounds_response_and_uses_single_homepage(self):
        class Response:
            body = degradation_html().encode()
            limit = None
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): self.limit = limit; return self.body
        response = Response()
        with patch.object(radar, 'urlopen', return_value=response) as request:
            result = radar.fetch_degradation(radar.SOURCE_URL)
            self.assertEqual(len(result['points']), 46)
            self.assertEqual(response.limit, radar.MAX_RESPONSE_BYTES+1)
            self.assertEqual(request.call_args.kwargs['timeout'], 20)
            self.assertEqual(request.call_args.args[0].get_header('Accept'), 'text/html')
            response.body = b'x'*(radar.MAX_RESPONSE_BYTES+1)
            with self.assertRaises(ValueError): radar.fetch_degradation(radar.SOURCE_URL)


class RequestRetryTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.service = radar.RadarService(Path(self.directory.name)/'cache.json')
        self.addCleanup(self.service.close)

    def test_transient_retries_are_bounded_and_success_clears_errors(self):
        fetcher = unittest.mock.Mock(side_effect=[TimeoutError('timed out'),
            radar.URLError(ConnectionResetError('reset')), degradation_fixture()])
        self.service._fetcher = fetcher
        with patch.object(self.service._wake, 'wait', return_value=False) as wait:
            self.assertTrue(self.service.refresh_if_due(force=True))
        self.assertEqual(fetcher.call_count, 3)
        self.assertEqual([c.args[0] for c in wait.call_args_list], [1, 3])
        self.assertIsNone(self.service.snapshot()['last_error'])

    def test_retry_exhaustion_keeps_snapshot_and_uses_scheduled_backoff(self):
        self.service._fetcher = lambda _: degradation_fixture()
        self.service.refresh_if_due()
        before = self.service.snapshot()
        fetcher = unittest.mock.Mock(side_effect=TimeoutError('offline'))
        self.service._fetcher = fetcher
        with patch.object(self.service._wake, 'wait', return_value=False):
            self.assertFalse(self.service.refresh_if_due(force=True))
        self.assertEqual(fetcher.call_count, 3)
        self.assertEqual(self.service.snapshot()['data'], before['data'])
        self.assertEqual(self.service.snapshot()['fetched_at'], before['fetched_at'])
        self.assertTrue(self.service.snapshot()['stale'])

    def test_http_retries_only_temporary_gateway_errors(self):
        for code, calls in ((502,3), (503,3), (504,3), (403,1), (404,1), (429,1)):
            with self.subTest(code=code):
                fetcher = unittest.mock.Mock(side_effect=radar.HTTPError(radar.SOURCE_URL,code,'error',{},None))
                self.service._fetcher = fetcher
                with patch.object(self.service._wake,'wait',return_value=False):
                    self.assertFalse(self.service.refresh_if_due(force=True))
                self.assertEqual(fetcher.call_count,calls)
        for error in (ValueError('schema changed'),radar.URLError(radar.ssl.SSLCertVerificationError('certificate'))):
            fetcher = unittest.mock.Mock(side_effect=error)
            self.service._fetcher = fetcher
            self.assertFalse(self.service.refresh_if_due(force=True))
            fetcher.assert_called_once()

    def test_pause_during_retry_wait_prevents_another_request(self):
        fetcher = unittest.mock.Mock(side_effect=TimeoutError('offline'))
        self.service._fetcher = fetcher
        with patch.object(self.service._wake,'wait',side_effect=lambda _: self.service.set_enabled(False)):
            self.assertFalse(self.service.refresh_if_due(force=True))
        fetcher.assert_called_once()


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "radar.json"
        self.now = 1788782400.0
        self.calls = []
        self.error = None
        self.service = radar.RadarService(self.path, clock=lambda: self.now, fetcher=self.fetch)
        self.addCleanup(self.service.close)

    def fetch(self, url):
        self.calls.append(url)
        if self.error:
            raise self.error
        self.assertEqual(url, radar.SOURCE_URL)
        return degradation_fixture()

    def test_reads_never_fetch_and_four_hour_expiry_survives_restart(self):
        self.assertFalse(self.service.snapshot()["available"])
        self.assertEqual(self.calls, [])
        self.assertTrue(self.service.refresh_if_due())
        for _ in range(20):
            self.service.snapshot()
        self.now += radar.REFRESH_SECONDS - 1
        restarted = radar.RadarService(self.path, clock=lambda: self.now, fetcher=self.fetch)
        self.assertFalse(restarted.refresh_if_due())
        self.assertEqual(len(self.calls), 1)
        self.now += 1
        self.assertTrue(restarted.refresh_if_due())
        self.assertEqual(len(self.calls), 2)
        # Windows stat modes do not express POSIX owner/group permissions.
        # Cache creation and restart behavior above are checked on every OS.
        if os.name == "posix":
            self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_failure_preserves_snapshot_and_persists_retry_backoff(self):
        self.service.refresh_if_due()
        before = self.service.snapshot()
        self.now += radar.REFRESH_SECONDS
        self.error = ValueError("upstream changed")
        self.assertFalse(self.service.refresh_if_due())
        failed = self.service.snapshot()
        self.assertEqual(before["data"], failed["data"])
        self.assertEqual(before["fetched_at"], failed["fetched_at"])
        self.assertTrue(failed["stale"])
        count = len(self.calls)
        restarted = radar.RadarService(self.path, clock=lambda: self.now, fetcher=self.fetch)
        self.assertFalse(restarted.refresh_if_due())
        self.assertEqual(len(self.calls), count)
        self.now += radar.RETRY_SECONDS
        self.error = None
        self.assertTrue(restarted.refresh_if_due())
        self.assertFalse(restarted.snapshot()["stale"])
        self.assertIsNone(restarted.snapshot()["last_error"])

    def test_old_formats_are_hidden_and_retry_recovers_without_mixing_scores(self):
        for version in (1, 2, 3, 4, 5, radar.CACHE_VERSION):
            with self.subTest(version=version):
                snapshot = legacy_snapshot("radar-bench-v2-150" if version >= 4 else None)
                self.path.write_text(json.dumps({"schema_version":version, "snapshot":snapshot,
                    "fetched_at_epoch":self.now, "next_attempt_at_epoch":self.now+radar.REFRESH_SECONDS, "failures":5}))
                service = radar.RadarService(self.path, clock=lambda:self.now, fetcher=self.fetch)
                self.assertFalse(service.snapshot()["available"])
                self.assertIsNone(service.snapshot()["data"])
                self.error = OSError("offline")
                self.assertFalse(service.refresh_if_due())
                restarted = radar.RadarService(self.path, clock=lambda:self.now, fetcher=self.fetch)
                self.assertFalse(restarted.snapshot()["available"])
                count = len(self.calls)
                self.assertFalse(restarted.refresh_if_due())
                self.assertEqual(len(self.calls), count)
                self.now += radar.RETRY_SECONDS
                self.error = None
                self.assertTrue(restarted.refresh_if_due())
                self.assertEqual(restarted.snapshot()["data"]["benchmark_kind"], radar.DEGRADATION_KIND)
                self.assertEqual(json.loads(self.path.read_text())["schema_version"], radar.CACHE_VERSION)

    def test_parser_upgrade_refreshes_immediately_and_retains_current_scores(self):
        snapshot = degradation_fixture()
        self.path.write_text(json.dumps({'schema_version':6, 'snapshot':snapshot,
            'fetched_at_epoch':self.now, 'next_attempt_at_epoch':self.now+radar.REFRESH_SECONDS, 'failures':5}))
        upgraded = radar.RadarService(self.path, clock=lambda:self.now, fetcher=self.fetch)
        self.assertEqual(upgraded.snapshot()['data'], snapshot)
        self.error = ValueError('invalid response')
        self.assertFalse(upgraded.refresh_if_due())
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(upgraded.snapshot()['data'], snapshot)
        restarted = radar.RadarService(self.path, clock=lambda:self.now, fetcher=self.fetch)
        self.assertFalse(restarted.refresh_if_due())
        self.assertEqual(len(self.calls), 1)
        self.now += radar.RETRY_SECONDS
        self.error = None
        self.assertTrue(restarted.refresh_if_due())
        self.assertFalse(restarted.snapshot()['stale'])

    def test_older_test_round_never_replaces_latest_snapshot(self):
        self.service.refresh_if_due()
        before = self.service.snapshot()['data']
        self.service._fetcher = lambda _: radar.degradation_snapshot(degradation_html().replace('2026-10-31','2026-10-30'))
        self.assertFalse(self.service.refresh_if_due(force=True))
        self.assertEqual(self.service.snapshot()['data'], before)

    def test_partial_fetch_never_replaces_good_snapshot(self):
        self.service.refresh_if_due()
        before = self.service.snapshot()["data"]
        original = self.service._fetcher
        self.service._fetcher = lambda url: {"schema": 999}
        self.assertFalse(self.service.refresh_if_due(force=True))
        self.assertEqual(self.service.snapshot()["data"], before)

    def test_repeated_failure_backs_off_and_caps_at_four_hours(self):
        self.error = OSError("offline")
        for minutes in (15, 30, 60, 120, 240, 240):
            self.assertFalse(self.service.refresh_if_due())
            state = json.loads(self.path.read_text())
            self.assertEqual(state["next_attempt_at_epoch"] - self.now, minutes * 60)
            self.now = state["next_attempt_at_epoch"]

    def test_cache_read_and_duplicate_refresh_do_not_wait_for_network(self):
        started, release = threading.Event(), threading.Event()
        original = self.service._fetcher
        def slow(url):
            started.set()
            release.wait(timeout=3)
            return original(url)
        self.service._fetcher = slow
        worker = threading.Thread(target=self.service.refresh_if_due)
        worker.start()
        try:
            self.assertTrue(started.wait(timeout=1))
            self.assertTrue(self.service.snapshot()["refreshing"])
            self.assertFalse(self.service.refresh_if_due(force=True))
        finally:
            release.set()
            worker.join(timeout=3)
        self.assertTrue(self.service.snapshot()["available"])

    def test_worker_fetches_without_a_browser_request_and_stops(self):
        saved = threading.Event()
        original = radar.atomic_write
        def write(*args):
            original(*args)
            saved.set()
        with patch.object(radar, "atomic_write", side_effect=write):
            self.service.start()
            self.assertTrue(saved.wait(timeout=2))
            self.service.close()
        self.assertFalse(self.service._thread.is_alive())
        self.assertEqual(len(self.calls), 1)

    def test_corrupt_cache_recovers_and_disk_failure_keeps_live_data(self):
        self.path.write_text('{"broken":')
        service = radar.RadarService(self.path, clock=lambda: self.now, fetcher=self.fetch)
        self.assertFalse(service.snapshot()["available"])
        with patch.object(radar, "atomic_write", side_effect=OSError("read-only")):
            self.assertTrue(service.refresh_if_due())
        self.assertTrue(service.snapshot()["available"])
        self.assertIsNotNone(service.snapshot()["cache_warning"])

    def test_incomplete_current_scores_do_not_break_startup(self):
        snapshot = degradation_fixture()
        del snapshot["points"][0]["score"]
        self.path.write_text(json.dumps({"schema_version":radar.CACHE_VERSION, "snapshot":snapshot,
            "fetched_at_epoch":self.now, "next_attempt_at_epoch":self.now+radar.REFRESH_SECONDS}))
        service = radar.RadarService(self.path, clock=lambda:self.now, fetcher=self.fetch)
        self.assertFalse(service.snapshot()["available"])
        self.assertTrue(service.refresh_if_due())
        self.assertTrue(service.snapshot()["available"])

    def test_invalid_cache_times_cannot_crash_or_postpone_recovery(self):
        snapshot = degradation_fixture()
        for timestamp in (float("inf"), 1e30, "bad", -1, None):
            with self.subTest(timestamp=timestamp):
                self.path.write_text(json.dumps({"schema_version": radar.CACHE_VERSION, "snapshot": snapshot,
                    "fetched_at_epoch": timestamp, "next_attempt_at_epoch": timestamp}))
                service = radar.RadarService(self.path, clock=lambda: self.now, fetcher=self.fetch)
                self.assertFalse(service.snapshot()["available"])
                self.assertTrue(service.refresh_if_due())

    def test_nonfinite_cache_metadata_cannot_break_failure_retries(self):
        self.service.refresh_if_due()
        state = json.loads(self.path.read_text())
        state["unexpected_metadata"] = float("nan")
        self.path.write_text(json.dumps(state))
        restarted = radar.RadarService(self.path, clock=lambda: self.now, fetcher=self.fetch)
        self.assertFalse(restarted.snapshot()["available"])
        self.error = OSError("offline")
        self.assertFalse(restarted.refresh_if_due())
        self.now += radar.RETRY_SECONDS
        self.error = None
        self.assertTrue(restarted.refresh_if_due())


class WorkerToggleTest(unittest.TestCase):
    def test_paused_worker_never_fetches_and_resume_keeps_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            fetcher = unittest.mock.Mock(side_effect=RuntimeError('synthetic offline'))
            service = radar.RadarService(Path(directory)/'cache.json', fetcher=fetcher)
            service.set_enabled(False)
            self.assertFalse(service.refresh_if_due(force=True))
            fetcher.assert_not_called()
            service.set_enabled(True)
            service.refresh_if_due(force=True)
            self.assertTrue(fetcher.called)
            before = service.snapshot()
            service.set_enabled(False)
            self.assertEqual(service.snapshot(), before)


@unittest.skipUnless(shutil.which("node"), "Node.js is needed for renderer regression tests")
class RadarRendererTest(unittest.TestCase):
    def render_script(self, script):
        # Execute the actual pure renderer helpers; no browser or account state.
        start = radar.SCRIPT.index("      const models =")
        end = radar.SCRIPT.index("      function render()")
        return subprocess.run(
            [shutil.which("node")], input=radar.SCRIPT[start:end] + "\n" + script,
            text=True, encoding="utf-8", capture_output=True, check=True, timeout=5,
        ).stdout

    def test_score_meters_use_fixed_150_scale_not_family_maximum(self):
        snapshot = degradation_fixture()
        values = [None, 0, 75, 107.3, 150]
        for point, value in zip(snapshot['points'], values):
            point['score'] = value
        html = self.render_script('process.stdout.write(benchCards('+json.dumps(snapshot['points'])+'));')
        tree = ET.fromstring('<root>'+html+'</root>')
        cards = {b.get('data-radar-card'): b for b in tree.findall('./div/div/button')}
        for index, value in enumerate(values):
            card = cards[str(index)]
            meter = card.find("span[@aria-hidden='true']")
            fill = meter.find('span')
            if value is None:
                self.assertEqual(card.findtext('strong'), '—')
                self.assertIsNone(fill)
                self.assertIn('radar-meter--missing', meter.get('class'))
            else:
                self.assertEqual(card.findtext('strong'), f'{value:.2f}')
                width = float(fill.get('style').removeprefix('width:').removesuffix('%'))
                self.assertAlmostEqual(width, value / 150 * 100, places=4)
                self.assertIn('/ 150', card.get('aria-label'))
        sol = next(f for f in tree if f.findtext('h3')=='GPT-6.1 Sol')
        self.assertEqual([b.findtext('./span/span') for b in sol.findall('./div/button')],
                         ['ultra','max','xhigh','high','medium','low'])

    def test_score_cards_in_both_languages_have_no_chart_or_cost_controls(self):
        snapshot = degradation_fixture()
        result = json.loads(self.render_script('payload={data:'+json.dumps(snapshot)+'};'+"""
          const document={activeElement:null};
          root={clientWidth:390,contains:()=>false,querySelector:()=>({addEventListener:()=>{}})};
          const output=[];
          for (const language of ['en','zh']) {
            lang=language; renderBench(); output.push(root.innerHTML);
          }
          process.stdout.write(JSON.stringify(output));
        """))
        self.assertEqual(len(result), 2)
        for html in result:
            self.assertEqual(html.count('data-radar-card='), 46)
            self.assertEqual(html.count('class="radar-meter"'), 46)
            self.assertNotIn('RadarBench ·', html)
            for removed in ('data-radar-metric', 'data-radar-history-model', '<svg', 'API', 'USD', '费用', '耗时', 'NaN', 'Infinity', 'undefined'):
                self.assertNotIn(removed, html)
        self.assertIn('分数和条 = 官网总分 / 满分 150', result[1])

    def test_loading_failure_and_legacy_payload_never_render_old_scores(self):
        old = legacy_snapshot()
        current = degradation_fixture()
        cases = [None, {'data': None, 'last_error': 'offline'},
                 {'data': old, 'last_error': 'upgrade pending'},
                 {'data': current, 'stale': True, 'last_error': 'offline'}]
        output = self.render_script('const cases='+json.dumps(cases)+';'+"""
          const document={activeElement:null};
          root={clientWidth:390,contains:()=>false,querySelector:()=>({addEventListener:()=>{}})};
          process.stdout.write(JSON.stringify(cases.map(p=>{payload=p; renderBench(); return root.innerHTML;})));
        """)
        loading, failed, legacy, retained = json.loads(output)
        self.assertIn('Fetching the first benchmark snapshot', loading)
        self.assertIn('Benchmark data is temporarily unavailable', failed)
        for html in (loading, failed, legacy):
            self.assertNotIn('data-radar-card=', html)
            self.assertNotIn('data-radar-mode=', html)
        self.assertIn('Benchmark data is temporarily unavailable', legacy)
        self.assertEqual(retained.count('data-radar-card='), 46)
        self.assertIn('Showing the last successful snapshot', retained)

    def test_missing_and_zero_scores_remain_distinct_in_score_cards(self):
        snapshot = degradation_fixture()
        snapshot['points'][0].update(score=None)
        snapshot['points'][1].update(score=0)
        html = self.render_script('process.stdout.write(benchCards('+json.dumps(snapshot['points'])+'));')
        tree = ET.fromstring('<root>'+html+'</root>')
        buttons = tree.findall('./div/div/button')
        by_index = {b.get('data-radar-card'):b for b in buttons}
        self.assertEqual(by_index['0'].findtext('strong'), '—')
        self.assertIn('Not tested', by_index['0'].get('aria-label'))
        self.assertEqual(by_index['1'].findtext('strong'), '0.00')
        self.assertNotIn('Not tested', by_index['1'].get('aria-label'))


class RadarAPITest(unittest.TestCase):
    def test_authenticated_endpoint_reads_cache_without_upstream_work(self):
        with tempfile.TemporaryDirectory() as directory:
            service = radar.RadarService(Path(directory) / "cache.json", fetcher=lambda _: self.fail("API initiated network work"))
            server = web.create_server("127.0.0.1", 0, access_token="test-radar-token",
                                       allowed_hosts=["127.0.0.1"], max_workers=2,
                                       max_collectors=1, cache_seconds=5, radar_service=service)
            server.quiet = True
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for method, authorized, status in (("GET", False, 403), ("HEAD", False, 403),
                                                   ("GET", True, 200), ("HEAD", True, 200)):
                    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
                    headers = {"Authorization": "Bearer test-radar-token"} if authorized else {}
                    connection.request(method, "/api/codex-radar", headers=headers)
                    response = connection.getresponse()
                    body = response.read()
                    self.assertEqual(response.status, status)
                    if authorized and method == "GET":
                        self.assertFalse(json.loads(body)["available"])
                    connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
