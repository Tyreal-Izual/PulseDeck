"""Accounting, calendar boundaries, and incremental I/O regression cases."""
import json
import tempfile
import unittest
from datetime import date, timedelta, timezone
from pathlib import Path

from pulsedeck.local_usage import (
    CODEX_INDEX, CLAUDE_INDEX, TimeScope, aggregate, counts, timestamp,
)


def context(model="model-a", turn="turn-a"):
    return {"type": "turn_context", "payload": {"model": model, "turn_id": turn, "cwd": "/project"}}


def snapshot(total, last=None, when="2026-11-05T12:00:00Z"):
    info = {"total_token_usage": {"total_tokens": total}}
    if last is not None:
        info["last_token_usage"] = {"total_tokens": last}
    return {"type": "event_msg", "timestamp": when, "payload": {"type": "token_count", "info": info}}


def direct(total, usage, response, when="2026-11-05T12:00:00Z"):
    return {"type": "token_usage_record", "timestamp": when, "payload": {
        "response_id": response, "usage": {"total_tokens": usage},
        "thread_token_usage": {"total_tokens": total}}}


def claude(message, output=5, when="2026-11-05T12:00:00Z", model="model-a"):
    return {"type": "assistant", "sessionId": "session", "timestamp": when, "cwd": "/project",
            "message": {"id": message, "model": model, "content": "PRIVATE_SENTINEL",
                        "usage": {"input_tokens": 10, "output_tokens": output,
                                  "cache_read_input_tokens": 20, "cache_creation_input_tokens": 2}}}


class LocalUsageTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        CODEX_INDEX.entries.clear()
        CLAUDE_INDEX.entries.clear()

    def write(self, rows, source="codex", name="one", folder=None):
        path = self.home / (folder or ("sessions" if source == "codex" else "projects")) / (name + ".jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        return path

    def collect(self, source="codex", scope="all", top=10):
        return aggregate(self.home, source, top, scope, "2026-11-05")

    def test_direct_and_snapshot_merge_with_model_switch(self):
        self.write([context(), direct(100, 100, "r1"), snapshot(100, 100), snapshot(100, 100),
                    context("model-b", "turn-b"), snapshot(150, 50), direct(150, 50, "r2")])
        result = self.collect(scope="today")
        self.assertEqual(result["token_totals"]["total_tokens"], 150)
        self.assertEqual(result["unique_usage_records"], 2)
        self.assertEqual({r["model"]: r["total_tokens"] for r in result["by_model"]}, {"model-a": 100, "model-b": 50})

    def test_cumulative_baseline_is_not_assigned_to_observed_day_or_model(self):
        self.write([context(), snapshot(100), snapshot(150, 20)])
        all_usage, today = self.collect(), self.collect(scope="today")
        self.assertEqual(all_usage["token_totals"]["total_tokens"], 150)
        self.assertEqual(today["token_totals"]["total_tokens"], 20)
        self.assertEqual(today["quality"]["unknown_date_tokens"], 130)
        self.assertEqual(all_usage["quality"]["unknown_model_tokens"], 130)

    def test_counters_reset_and_may_revisit_an_old_endpoint(self):
        self.write([context(), snapshot(10, 10), snapshot(30, 20), snapshot(10, 10), snapshot(20, 10)])
        result = self.collect()
        self.assertEqual(result["token_totals"]["total_tokens"], 50)
        self.assertEqual(result["quality"]["counter_resets"], 1)

    def test_process_and_history_counters_have_different_baselines(self):
        self.write([context(), snapshot(1000, 1000), context("model-b", "turn-b"),
                    direct(20, 20, "new-1"), snapshot(1020, 20),
                    direct(50, 30, "new-2"), snapshot(1050, 30)])
        result = self.collect()
        self.assertEqual(result["token_totals"]["total_tokens"], 1050)
        self.assertEqual(result["quality"]["unknown_date_tokens"], 0)
        self.assertEqual(result["quality"]["counter_resets"], 0)
        self.assertEqual({r["model"]:r["total_tokens"] for r in result["by_model"]}, {"model-a":1000, "model-b":50})

    def test_same_snapshot_after_turn_switch_does_not_repeat_last_usage(self):
        self.write([context(), snapshot(10, 10), context("model-b", "turn-b"), snapshot(10, 10)])
        self.assertEqual(self.collect()["token_totals"]["total_tokens"], 10)

    def test_direct_without_cumulative_does_not_double_count_later_snapshot(self):
        row = direct(100, 100, "r1")
        del row["payload"]["thread_token_usage"]
        self.write([context(), row, snapshot(100, 100)])
        self.assertEqual(self.collect()["token_totals"]["total_tokens"], 100)

    def test_archived_and_copied_response_records_are_deduplicated(self):
        rows = [context(), direct(100, 100, "shared")]
        self.write(rows)
        self.write(rows + [direct(150, 50, "new")], name="copy", folder="archived_sessions")
        self.assertEqual(self.collect()["token_totals"]["total_tokens"], 150)

    def test_claude_streaming_retains_complete_usage_and_initial_date(self):
        first = claude("m1", 1, "2026-11-04T12:00:00Z")
        final = claude("m1", 10)
        final["requestId"] = "added-later"
        partial = {"type":"assistant", "message":{"id":"m1", "usage":{
            "input_tokens":10, "output_tokens":15, "cache_read_input_tokens":20, "cache_creation_input_tokens":2}}}
        self.write([first, final, first, partial], source="claude")
        self.write([final], source="claude", name="copy")
        result = self.collect("claude")
        self.assertEqual(result["token_totals"]["total_tokens"], 47)
        self.assertEqual(result["unique_usage_records"], 1)
        self.assertEqual(result["quality"]["unknown_date_tokens"], 0)
        self.assertEqual(result["quality"]["unknown_model_tokens"], 0)
        self.assertEqual(result["by_project"][0]["project"], "/project")
        self.assertEqual(self.collect("claude", "today")["token_totals"]["total_tokens"], 0)

    def test_calendar_ranges_apply_to_every_breakdown_for_both_sources(self):
        for source in ("codex", "claude"):
            rows = []
            for number, day in enumerate(("2026-10-01", "2026-10-07", "2026-10-30", "2026-11-05")):
                when = day + "T12:00:00Z"
                rows += [context(f"m{number}", f"t{number}"), direct((number + 1) * 10, 10, f"r{number}", when)] if source == "codex" else [claude(str(number), when=when, model=f"m{number}")]
            self.write(rows, source=source)
            for scope, number in (("today", 1), ("7d", 2), ("30d", 3), ("all", 4)):
                result = self.collect(source, scope)
                total = number * (10 if source == "codex" else 37)
                self.assertEqual(result["token_totals"]["total_tokens"], total)
                for key in ("by_model", "by_project", "daily_usage"):
                    self.assertEqual(sum(r["total_tokens"] for r in result[key]), total)
                self.assertEqual(sum(r["usage"]["total_tokens"] for r in result["top_sessions"]), total)
                self.assertEqual(result["model_count"], number)

    def test_cross_file_streaming_merge_preserves_known_metadata(self):
        partial = claude("m1", 10)
        del partial["message"]["model"]
        del partial["cwd"]
        self.write([partial], source="claude", name="a")
        self.write([claude("m1", 1, "2026-11-04T12:00:00Z")], source="claude", name="z")
        self.assertEqual(self.collect("claude")["token_totals"]["total_tokens"], 42)
        self.assertEqual(self.collect("claude")["quality"]["unknown_model_tokens"], 0)
        self.assertEqual(self.collect("claude")["by_project"][0]["project"], "/project")
        self.assertEqual(self.collect("claude", "today")["token_totals"]["total_tokens"], 0)

    def test_local_timezone_and_exact_calendar_boundaries(self):
        scope = TimeScope("today", date(2026, 11, 5), timezone(timedelta(hours=8)))
        self.assertFalse(scope.includes(timestamp("2026-11-04T15:59:59Z")))
        self.assertTrue(scope.includes(timestamp("2026-11-04T16:00:00Z")))
        self.assertTrue(scope.includes(timestamp("2026-11-05T15:59:59Z")))
        self.assertFalse(scope.includes(timestamp("2026-11-05T16:00:00Z")))
        self.assertFalse(scope.includes(None))

    def test_top_models_use_full_denominator_and_include_remainder(self):
        self.write([claude(str(n), model=f"m{n}") for n in range(13)], source="claude")
        result = self.collect("claude", top=3)
        self.assertEqual(len(result["by_model"]), 4)
        self.assertEqual(result["by_model"][-1]["model"], "__other__")
        self.assertAlmostEqual(sum(r["share"] for r in result["by_model"]), 100)
        self.assertEqual(sum(r["total_tokens"] for r in result["by_model"]), result["token_totals"]["total_tokens"])

    def test_cached_and_reasoning_details_are_not_added_twice(self):
        usage = counts({"input_tokens": 100, "cached_input_tokens": 50, "output_tokens": 20,
                        "reasoning_output_tokens": 15}, "codex")
        self.assertEqual(usage["total_tokens"], 120)
        self.assertIsNone(counts({"total_tokens": float("nan")}, "codex"))
        self.assertIsNone(counts({"total_tokens": -2}, "codex"))

    def test_incremental_append_reads_only_suffix_and_bounded_anchors(self):
        path = self.write([{"type": "user", "content": "PRIVATE_SENTINEL" * 1000}, claude("m1")], source="claude")
        first = self.collect("claude")
        second = self.collect("claude")
        self.assertGreater(first["refresh"]["bytes_read"], 10000)
        self.assertEqual(second["refresh"]["bytes_read"], 0)
        suffix = (json.dumps(claude("m2")) + "\n").encode()
        with path.open("ab") as handle:
            handle.write(suffix)
        third = self.collect("claude")
        self.assertEqual(third["token_totals"]["total_tokens"], 74)
        self.assertLessEqual(third["refresh"]["bytes_read"], len(suffix) + 1024)
        self.assertEqual(third["refresh"]["files_appended"], 1)
        state = CLAUDE_INDEX.entries[str(path)]
        self.assertNotIn("PRIVATE_SENTINEL", repr(vars(state.parser)))
        self.assertEqual(len(state.head), 32)

    def test_partial_utf8_line_is_retried_without_losing_previous_rows(self):
        path = self.write([claude("m1")], source="claude")
        self.collect("claude")
        second = claude("m2")
        second["message"]["content"] = "中文"
        raw = (json.dumps(second, ensure_ascii=False) + "\n").encode()
        cut = raw.index("中".encode()) + 1
        with path.open("ab") as handle:
            handle.write(raw[:cut])
        pending = self.collect("claude")
        self.assertEqual(pending["token_totals"]["total_tokens"], 37)
        self.assertEqual(pending["quality"]["pending_lines"], 1)
        self.assertEqual(pending["quality"]["parse_errors"], 0)
        with path.open("ab") as handle:
            handle.write(raw[cut:])
        self.assertEqual(self.collect("claude")["token_totals"]["total_tokens"], 74)

    def test_truncate_replace_delete_and_valid_unterminated_line(self):
        path = self.write([claude("m1"), claude("m2")], source="claude")
        self.collect("claude")
        path.write_text(json.dumps(claude("m3")), encoding="utf-8")
        self.assertEqual(self.collect("claude")["token_totals"]["total_tokens"], 37)
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\n" + json.dumps(claude("m4")) + "\n")
        self.assertEqual(self.collect("claude")["token_totals"]["total_tokens"], 74)
        replacement = path.with_suffix(".tmp")
        replacement.write_text(json.dumps(claude("m5")) + "\n", encoding="utf-8")
        replacement.replace(path)
        self.assertEqual(self.collect("claude")["token_totals"]["total_tokens"], 37)
        path.unlink()
        self.assertEqual(self.collect("claude")["token_totals"]["total_tokens"], 0)
        self.assertFalse(CLAUDE_INDEX.entries)

    def test_growing_rewrite_invalidates_anchors_instead_of_adding_old_data(self):
        path = self.write([claude("old")], source="claude")
        self.collect("claude")
        self.write([claude("replacement"), claude("additional")], source="claude")
        result = self.collect("claude")
        self.assertEqual(result["token_totals"]["total_tokens"], 74)
        self.assertEqual(result["refresh"]["files_rebuilt"], 1)
        self.assertNotIn("message:old", CLAUDE_INDEX.entries[str(path)].parser.rows)

    def test_malformed_metadata_does_not_discard_valid_events(self):
        self.write([{"type":[]}, {"type":"event_msg", "payload":{"type":{}}}, context(), snapshot(10, 10)])
        self.assertEqual(self.collect()["token_totals"]["total_tokens"], 10)


if __name__ == "__main__":
    unittest.main()
