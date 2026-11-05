# Local usage accounting (0.4)

PulseDeck reads Codex `sessions/` and `archived_sessions/`, and Claude
`projects/` JSONL files. It never calls account APIs, launches an auth client,
or uploads usage. Isambard and Radar remain separate public sources.

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
