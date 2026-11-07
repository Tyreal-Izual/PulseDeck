# Local usage accounting (0.4)

[English overview](../README.md) · [中文入门](../README.zh-CN.md)

PulseDeck reads Codex `sessions/` and `archived_sessions/`, and Claude
`projects/` JSONL files. These statistics never call account APIs, launch an auth client,
or upload usage. Reset Credits have the separate read-only exception below. Isambard and Radar remain separate public sources.

## One calendar range

Today, last 7 days, last 30 days (default), and all local history apply to
totals, model/project rankings, sessions, and the daily chart together.
The range includes today and uses the computer's local timezone and each
usage event's timestamp, not the filename date. Empty calendar days are zero.
Long charts group consecutive days into at most 60 bars without dropping usage.

`GET /api/sources` supplies `localDate`. Progressive source requests share it
as `range_anchor`, so crossing midnight during a refresh cannot split scopes.
The API returns `settings.scope` and each collector returns `usage.scope`
(Codex) or `local_usage.scope` (Claude). Source and report caches include the
range and anchor; changing selection cancels and ignores old results.

## Quota snapshots (0.4.1)

The homepage shows quota bars separately from history. Codex reads the latest
main-account `rate_limits` entry already present in `event_msg/token_count`
logs, using the same incremental index. Window duration identifies five-hour
versus seven-day limits, including weekly-only primary windows. Claude reads
its existing capture file. These local quota collectors do not start account requests.
Quotas ignore the history time filter. Countdown and snapshot-age labels tick
locally every second; new percentages arrive on the normal 15-second refresh
when the client has written a new snapshot. Missing windows display no value;
stale snapshots are labeled, and reaching a reset time hides the old percentage
until a new snapshot is available. A reset is never assumed to mean 100% remaining.

## Reset Credits (0.4.6)

Reset Credits alone use the documented Codex app-server `account/rateLimits/read`
method through the installed, signed-in client. The RPC sequence contains only
`initialize`, `initialized`, and that read method. The reply's other quota and
usage data are discarded. There is no account-history request, legacy HTTP
fallback, or redemption action. Protocol reference: [official OpenAI documentation](https://learn.chatgpt.com/docs/app-server).

The server coalesces requests and caches the result for 300 seconds, including
failed reads, so UI refresh and range switches do not generate repeated account
lookups. The available count is authoritative even if detail rows are capped or
missing. Null counts remain unavailable, not zero. The panel shows read time;
expiry countdowns tick locally. No Reset Credits snapshot is written to disk.

This exception is enabled by default in this version. Set
`PULSEDECK_RESET_CREDITS_ONLINE=0` before starting to disable it. The broader
`ACCOUNT_NETWORK_ENABLED` policy remains false.

## Accounting

- Codex prefers `token_usage_record.usage` per response. Legacy snapshots use
  cumulative differences and `last_token_usage`. Process counters and history
  counters can have different baselines; they are never subtracted from one
  another. Direct usage is reconciled against snapshot deltas, not added twice.
- Codex cached input is already included in input, and reasoning output in
  output. Those detail counters are not added again. Models follow the event's
  turn context, rather than assigning a whole SQLite thread to its latest model.
- Claude sums input, output, cache creation and cache read. Repeated message IDs
  retain the most complete usage and earliest timestamp, including across files.
- Response IDs and legacy counter identities deduplicate copied/archive records.
  Records without stable IDs use a metadata fallback; indistinguishable legacy
  events cannot always be resolved exactly.
- Unexplained cumulative baselines have unknown dates/models. All-history totals
  include them; finite ranges and charts exclude unknown dates. The UI shows the
  excluded amount. Rankings use the full selected total as their denominator,
  with an Other row beyond the requested model count.

Missing or pruned logs cannot be reconstructed. These are local recorded totals,
not billing totals or subscription quota. Data notes expose gaps, duplicates,
parse errors, pending lines and bytes read; scan diagnostics cover all local files.

## Incremental reads

The in-memory index retains only usage metadata, offsets, file identity, size,
mtime and SHA-256 prefix/tail anchors. No conversation text or token index is
written to disk. Unchanged files require no content reads. Appended files read
the suffix plus at most 1,024 bytes of anchor checks. Truncation, replacement,
changed anchors and completed unterminated lines rebuild the affected file.
Incomplete JSON/UTF-8 trailing lines are retried on the next append.

This is optimized for append-only logs. An in-place edit that preserves file
identity, size and mtime, or changes only the middle while preserving append
anchors, is not guaranteed to be detected until restart. Restarting rebuilds
the index from disk. Deleted files are removed from totals.

Legacy root CLI `--days` still limits daily display rows; the dashboard/API
uses `range=today|7d|30d|all` for consistent filtering.
