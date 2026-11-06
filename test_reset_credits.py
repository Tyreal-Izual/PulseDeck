"""Only the approved read RPC is sent; no account-history or redeem fallback."""
import json
from pathlib import Path
import queue
import unittest
from unittest.mock import patch

import codex_usage
from pulsedeck import codex_rpc


class FakeCodex:
    def __init__(self, limits, error=None):
        self.limits=limits
        self.error=error
        self.sent=[]
        self.closed=False
        self.waited=False
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
            reply={'error':self.error} if self.error and message['method']=='account/rateLimits/read' else {'result':result}
            self.responses.put(json.dumps({'id':message['id'],**reply})+'\n')

    def flush(self):pass
    def close(self):
        self.closed=True
        self.responses.put(None)
    def wait(self, timeout=None):
        self.waited=True
        return 0


class ResetCreditsScopeTest(unittest.TestCase):
    def collect(self, limits, error=None):
        process=FakeCodex(limits,error)
        with patch('pulsedeck.privacy.RESET_CREDITS_NETWORK_ENABLED',True), patch('pulsedeck.privacy.ACCOUNT_NETWORK_ENABLED',False), \
             patch.object(codex_rpc,'find_binary',return_value=Path('codex.exe')), patch.object(codex_rpc.subprocess,'Popen',return_value=process), \
             patch.object(codex_usage,'load_auth',side_effect=AssertionError('legacy credentials')):
            result=codex_usage.collect_resets()
        self.assertEqual([r['method'] for r in process.sent],['initialize','initialized','account/rateLimits/read'])
        self.assertTrue(process.closed)
        self.assertTrue(process.waited)
        self.assertIsNone(process.stdout.gi_frame)
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

    def test_rpc_errors_and_invalid_replies_are_redacted_and_close_client(self):
        for reply,error in (({}, {'code':401,'message':'PRIVATE_SERVER_ERROR'}), ([], None), (None, None)):
            with self.subTest(reply=reply,error=error):
                result=self.collect(reply,error)
                self.assertFalse(result['ok'])
                self.assertNotIn('PRIVATE_SERVER_ERROR',json.dumps(result))
                self.assertIn('Reset Credits could not be read',result['error']['message'])

    def test_timeout_closes_client_without_trying_another_account_method(self):
        with patch.object(codex_rpc.time,'monotonic',side_effect=[0,1,1000]):
            result=self.collect({})
        self.assertFalse(result['ok'])


if __name__=='__main__':unittest.main()
