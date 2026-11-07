# Privacy and limitations

[English overview](../README.md) · [中文入门](../README.zh-CN.md)

- The server listens on `127.0.0.1` by default.
- Codex and Claude transcript/state files are read but not modified; the Claude
  bridges write only the sanitised usage snapshot and refresher support files.
- Claude streaming rows are deduplicated before token totals are calculated.
- The Claude statusLine bridge never reads or reuses Claude OAuth credentials.
- The separate, optional macOS CLI refresher runs the normal Claude Code client and may perform its
  usual startup network requests or configured hooks, but sends no prompt and
  does not resume a conversation or save its terminal output. PulseDeck does not
  start this helper or an auth-status client.
- Reset Credits alone allow a read-only `account/rateLimits/read` request through
  the installed Codex client, at most once per five minutes per running server.
  PulseDeck does not consume resets or read/export credentials itself.
- Profile, account token-history, Admin API and legacy HTTP account requests stay
  disabled, including when API keys are configured. Set
  `PULSEDECK_RESET_CREDITS_ONLINE=0` to disable the reset-credit exception too.
- Quota bars read snapshots already on disk. Missing or expired windows are
  never assumed to have 100% remaining. The countdown updates locally.
- Isambard data comes from public status pages; only parsed cache data is kept.
- Radar requests only public benchmark metadata, sends no local account or
  conversation data, and stores its snapshot in a Git-ignored cache file.
- Individual collectors fail independently so one unavailable source does not
  take down the whole dashboard.

The other inactive upstream cloud adapters remain separate from the current local
collectors. Treat local totals and captured quotas as operational information
rather than a contractual billing statement. Do not commit API
keys, `auth.json`, private exports, cached account data, or sensitive
screenshots.
