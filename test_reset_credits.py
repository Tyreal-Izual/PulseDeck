"""Only the approved read RPC is sent; no account-history or redeem fallback."""
import json
from pathlib import Path
import queue
import unittest
from unittest.mock import patch

import codex_usage
from pulsedeck import codex_rpc


class FakeCodex:
    def __init__(self, limits):
        self.limits=limits
        self.sent=[]
        self.responses=queue.Queue()
        self.stdin=self
        self.stdout=self.lines()

    def lines(self):
        while True:
            response=self.responses.get(timeout=3)
            if response is None:return
            yield response

    def write(self, line):
        message=json.loads(line)
        self.sent.append(message)
        if 'id' in message:
            result=self.limits if message['method']=='account/rateLimits/read' else {}
            self.responses.put(json.dumps({'id':message['id'],'result':result})+'\n')

    def flush(self):pass
    def close(self):self.responses.put(None)
    def wait(self, timeout=None):return 0


class ResetCreditsScopeTest(unittest.TestCase):
    def collect(self, limits):
        process=FakeCodex(limits)
        with patch('pulsedeck.privacy.RESET_CREDITS_NETWORK_ENABLED',True), patch('pulsedeck.privacy.ACCOUNT_NETWORK_ENABLED',False), \
             patch.object(codex_rpc,'find_binary',return_value=Path('codex.exe')), patch.object(codex_rpc.subprocess,'Popen',return_value=process), \
             patch.object(codex_usage,'load_auth',side_effect=AssertionError('legacy credentials')):
            result=codex_usage.collect_resets()
        self.assertEqual([r['method'] for r in process.sent],['initialize','initialized','account/rateLimits/read'])
        return result

    def test_only_reset_count_and_redacted_details_are_returned(self):
        result=self.collect({'rateLimits':{'private':'DO_NOT_EXPORT'},'usage':{'private':'DO_NOT_EXPORT'},
            'rateLimitResetCredits':{'availableCount':3,'credits':[{'id':'PRIVATE_CREDIT_ID',
            'resetType':'codexRateLimits','status':'available','grantedAt':1781654400,'expiresAt':None}]}})
        self.assertEqual(result['available_count'],3)
        self.assertEqual(len(result['credits']),1)
        self.assertNotIn('DO_NOT_EXPORT',json.dumps(result))
        self.assertNotIn('PRIVATE_CREDIT_ID',json.dumps(result))

    def test_missing_reset_field_is_unavailable_without_another_endpoint(self):
        result=self.collect({'rateLimits':{'credits':{'balance':100}}})
        self.assertTrue(result['ok'])
        self.assertIsNone(result['available_count'])
        self.assertEqual(result['reason'],'not_provided')


if __name__=='__main__':unittest.main()
