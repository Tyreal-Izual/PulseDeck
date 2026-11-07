# Claude Code Setup

[English overview](../README.md) · [简体中文](claude-setup.zh-CN.md)

### Local token history

No installation step is required for token history. `claude_usage.py` reads
usage metadata from:

```text
~/.claude/projects/**/*.jsonl
```

Prompt text, response text, tool inputs, and file contents are ignored. Claude
Desktop Code sessions are included when the app writes them to this same
directory.

### Official 5-hour and 7-day windows

On Windows, run **Setup-Claude-Capture.cmd** from the project folder.
The script preserves an existing custom statusLine. The source command below is
also available to register the bridge for a compatible Claude Code client:

```sh
python3 claude_usage_statusline.py --install
```

After a compatible Claude Code client completes a response, the bridge writes
a sanitised snapshot to:

```text
~/.claude/usage-dashboard.json
```

It stores only rate-limit percentages, reset timestamps, model metadata, and
capture metadata. It does not store prompts or responses. Installation refuses
to replace a different statusLine unless `--force` is explicitly supplied.

Useful commands:

```sh
python3 claude_usage.py
python3 claude_usage.py --json --days 30 --top 10
python3 claude_usage_statusline.py --status
python3 claude_usage_statusline.py --uninstall
```

> Browser auto-refresh only rereads the latest snapshot. Claude Desktop may
> update local JSONL token history without invoking a custom statusLine. In
> that case, token charts continue to change while the 5-hour/7-day snapshot
> becomes stale. The dashboard displays snapshot age and stale state so an old
> value is not mistaken for live account usage.

PulseDeck does not run `claude auth status`, start a hidden Claude session, or
query Claude account endpoints. Missing snapshots remain unavailable; signing
in or refreshing the dashboard alone does not create a quota capture.

### Optional standalone refresher on macOS

This separate CLI helper is not started by PulseDeck and is not part of the
Windows desktop runtime. Running or installing it is an explicit user action;
the normal Claude client may make its own network requests.

`claude_usage_refresher.py` opens a temporary empty Claude Code session for this
repository, runs Claude Code's local `/usage` command, parses only the 5-hour
and weekly percentages/reset times, writes the same sanitised snapshot format,
and exits with `Ctrl-D`. `/usage` reads plan limits without submitting a prompt
to the model. The refresher does not resume a conversation or retain terminal
output, and it can work independently of the statusLine bridge. Claude Code
must already be signed in and this repository must have been trusted once.
For this temporary process only, the refresher disables Remote Control and
enables Claude's screen-reader output; it does not change the user's global
settings. It waits up to 30 seconds for an explicit interactive prompt, waits
one additional second for the prompt to settle, and only then sends `/usage`.
If the screen updates while local activity is scanned, the parser keeps the
latest complete, explicitly labelled value for each subscription window. It
never assigns an unlabelled incremental update to a window by position.

Test one refresh first:

```sh
python3 claude_usage_refresher.py --once --force
```

Install a per-user LaunchAgent with reset-aware refresh:

```sh
python3 claude_usage_refresher.py --install
python3 claude_usage_refresher.py --status
```

Remove it with:

```sh
python3 claude_usage_refresher.py --uninstall
```

The LaunchAgent performs a lightweight local snapshot check every 60 seconds;
it does not start Claude Code on every probe. Normal full refreshes remain
about ten minutes apart. When either stored reset deadline passes, the agent
waits 30 seconds for account state to settle and then prioritises one refresh,
so a dashboard stuck at `Resets in now` normally clears within 30–90 seconds.
A small `usage-dashboard-refresh-state.json` file records only attempt timing,
the reset timestamp, exit state, and consecutive-failure count. Any failed or
interrupted full refresh backs off for 5, 10, 20, and then at most 40 minutes,
so a broken `/usage` parser cannot launch Claude every minute. Available
subscription windows are parsed independently; one missing or invalid window
does not discard a valid one. Percentages outside 0–100 are rejected rather
than clamped. The existing process lock prevents overlap, and a stuck Claude
process is terminated. Logs remain under `~/.claude/usage-refresh*.log`.

The job runs only while the Mac is awake and logged in. Re-run `--install`
after upgrading from the older ten-minute scheduler, moving this repository,
or moving the Claude executable. This is client automation rather than an
Anthropic background-usage API, so a future Claude Code release may require
adjustments.
