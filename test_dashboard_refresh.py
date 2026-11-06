from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

import codex_claude_usage_web as web


@unittest.skipUnless(shutil.which('node'), 'Node.js is needed for renderer regression tests')
class ProgressiveRefreshTest(unittest.TestCase):
    def run_js(self, code):
        script = Path(__file__).with_name('static').joinpath('refresh.js').read_text(encoding='utf-8')
        result = subprocess.run([shutil.which('node')], input=script+'\n'+code,
                                text=True, encoding="utf-8", capture_output=True, timeout=10, check=True)
        return json.loads(result.stdout)

    def test_fast_local_results_arrive_before_slow_public_status_and_force_only_isambard(self):
        result = self.run_js('''
        const requests = [], updates = [];
        let finishPublic;
        const blocked = new Promise(resolve => finishPublic = resolve);
        global.fetch = async (url, options) => {
          const report = new URL(url, 'http://local').searchParams.get('report');
          requests.push({report, method:options.method || 'GET', headers:options.headers});
          if (report === 'isambard-status') await blocked;
          return {ok:true,status:200,json:async()=>({ok:true,data:{report}})};
        };
        const promise = DashboardRefresh.run({report:'all',days:'30',sources:['codex','claude','isambard'],force:true}, p => {
          updates.push(JSON.parse(JSON.stringify(p)));
          if (p.data.local_usage && p.pending.includes('isambard_status')) finishPublic();
        });
        promise.then(last=>process.stdout.write(JSON.stringify({requests,updates,last})));
        ''')
        self.assertTrue(any(u['data'].get('local_usage') and 'isambard_status' in u['pending'] for u in result['updates']))
        self.assertFalse(result['last']['pending'])
        self.assertTrue(result['last']['ok'])
        for request in result['requests']:
            self.assertEqual(request['method'], 'POST' if request['report']=='isambard-status' else 'GET')
        self.assertEqual(len(result['requests']), 3)

    def test_disabled_sources_make_no_requests_and_failures_stay_local(self):
        result = self.run_js('''
        const requests=[];
        global.fetch=async url=>{
          const report=new URL(url,'http://local').searchParams.get('report'); requests.push(report);
          if(report==='claude-usage')throw new Error('unreadable');
          return {ok:true,status:200,json:async()=>({ok:true,data:{report}})};
        };
        DashboardRefresh.run({report:'all',days:'30',sources:['codex','claude'],force:false},()=>{})
          .then(last=>process.stdout.write(JSON.stringify({requests,last})));
        ''')
        self.assertEqual(set(result['requests']), {'local-usage','claude-usage'})
        self.assertEqual(result['last']['data']['local_usage']['report'], 'local-usage')
        self.assertEqual(result['last']['errors'], [{'section':'claude_usage','message':'unreadable'}])
        self.assertTrue(result['last']['data']['isambard_status']['disabled'])
        self.assertTrue(result['last']['data']['reset_credits']['disabled'])

    def test_inflight_requests_are_bounded(self):
        result = self.run_js('''
        let active=0, max=0;
        global.fetch=async()=>{
          active++;max=Math.max(max,active);
          await new Promise(resolve=>setTimeout(resolve,5));active--;
          return {ok:true,status:200,json:async()=>({ok:true,data:{}})};
        };
        DashboardRefresh.run({report:'all',days:'30',sources:['codex','claude','isambard']},()=>{})
          .then(()=>process.stdout.write(JSON.stringify({max})));
        ''')
        self.assertEqual(result['max'], 2)

    def test_default_get_does_not_force_public_cache(self):
        result = self.run_js('''
        let request;
        global.fetch=async(url,options)=>{
          request={url,method:options.method||'GET'};
          return {ok:true,status:200,json:async()=>({ok:true,data:{}})};
        };
        DashboardRefresh.run({report:'isambard-status',days:'30',sources:['isambard'],force:false},()=>{})
          .then(()=>process.stdout.write(JSON.stringify(request)));
        ''')
        self.assertEqual(result['method'], 'GET')
        self.assertNotIn('isambard_force_refresh', result['url'])

    def test_history_stays_local_when_reset_credit_exception_is_enabled(self):
        result = self.run_js('''
        const requests=[];
        global.fetch=async url=>{
          requests.push(Object.fromEntries(new URL(url,'http://local').searchParams));
          return {ok:true,status:200,json:async()=>({ok:true,data:{}})};
        };
        DashboardRefresh.run({report:'all',range:'7d',rangeAnchor:'2026-10-01',days:'30',
          sources:['codex','claude'],resetCreditsNetworkEnabled:true},()=>{})
          .then(last=>process.stdout.write(JSON.stringify({requests,last})));
        ''')
        self.assertEqual({r['report'] for r in result['requests']}, {'local-usage','claude-usage','resets'})
        self.assertTrue(all(r['range']=='7d' and r['range_anchor']=='2026-10-01' for r in result['requests']))
        self.assertEqual(result['last']['range'], '7d')

    def test_cancelled_refresh_stops_queued_source_requests(self):
        result = self.run_js("""
        const controller = new AbortController(), requests=[];
        global.fetch=async (url, options)=>{
          requests.push(url);
          return new Promise((resolve,reject)=>{
            options.signal.addEventListener('abort',()=>reject(new DOMException('Cancelled','AbortError')));
          });
        };
        const running=DashboardRefresh.run({report:'all',days:'30',sources:['codex','claude','isambard'],signal:controller.signal},()=>{});
        controller.abort();
        running.then(()=>process.stdout.write(JSON.stringify({count:requests.length})));
        """)
        self.assertEqual(result['count'], 2)

    def test_assembled_dashboard_and_maintenance_scripts_parse(self):
        for html in (web.INDEX_HTML.replace('__DASHBOARD_CONFIG__', '{}').replace('__DEFAULT_REFRESH__','15'), web.MAINTENANCE_HTML):
            scripts = re.findall(r'<script>(.*?)</script>', html, re.S)
            self.assertTrue(scripts)
            for script in scripts:
                result = subprocess.run([shutil.which('node'), '--check'], input=script,
                                        text=True, encoding="utf-8", capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotRegex(html, r'__[A-Z_]+__')
