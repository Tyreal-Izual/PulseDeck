from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest

import claude_usage


class ClaudeTranscriptTest(unittest.TestCase):
    def test_streaming_and_cross_file_duplicates_are_counted_once(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            project = home / 'projects' / 'example'
            project.mkdir(parents=True)
            row = {'type': 'assistant', 'timestamp': '2026-10-05T00:00:00Z',
                   'requestId': 'request-1', 'message': {'id': 'message-1', 'model': 'example',
                   'usage': {'input_tokens': 10, 'output_tokens': 5,
                             'cache_creation_input_tokens': 2, 'cache_read_input_tokens': 3}}}
            encoded = json.dumps(row)+'\n'
            (project/'one.jsonl').write_text(encoded*2+'broken\n')
            subagent = project/'subagents'
            subagent.mkdir()
            (subagent/'two.jsonl').write_text(encoded)
            result = claude_usage.aggregate_local_usage(home, 10, 30)
            self.assertEqual(result['unique_usage_records'], 1)
            self.assertEqual(result['duplicate_usage_records_skipped'], 2)
            self.assertEqual(result['token_totals']['total_tokens'], 20)
            self.assertEqual(result['parse_or_read_errors'], 1)

    def test_cache_reuses_unchanged_and_refreshes_appended_files(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            project = home / 'projects'
            project.mkdir()
            file = project/'one.jsonl'
            row = {'type':'assistant','timestamp':'2026-10-05T00:00:00Z',
                   'message':{'id':'1','usage':{'input_tokens':10}}}
            file.write_text(json.dumps(row)+'\n')
            first = claude_usage.aggregate_local_usage(home, 10, 30)
            second = claude_usage.aggregate_local_usage(home, 10, 30)
            self.assertGreater(first['refresh']['bytes_read'], 0)
            self.assertEqual(second['refresh']['bytes_read'], 0)
            row['message']['id'] = '2'
            with file.open('a') as handle: handle.write(json.dumps(row)+'\n')
            result = claude_usage.aggregate_local_usage(home, 10, 30)
            self.assertEqual(result['refresh']['files_appended'], 1)
            self.assertEqual(result['token_totals']['total_tokens'], 20)
            file.unlink()
            self.assertEqual(claude_usage.aggregate_local_usage(home, 10, 30)['unique_usage_records'], 0)

    def test_missing_projects_is_a_clean_empty_state(self):
        with tempfile.TemporaryDirectory() as directory:
            result = claude_usage.aggregate_local_usage(Path(directory), 10, 30)
        self.assertFalse(result['available'])
        self.assertEqual(result['token_totals']['total_tokens'], 0)


if __name__ == "__main__":
    unittest.main()
