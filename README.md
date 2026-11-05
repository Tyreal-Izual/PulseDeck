# PulseDeck

> Current policy (0.2): Codex/Claude account collection is LOCAL ONLY. App-server, legacy backend and Admin API account requests are disabled. Claude snapshots are read from disk; no auth-status client is started. Isambard/Radar public fetches remain enabled. The disabled cloud adapters are retained only for possible future development.

**Your local dashboard for AI usage, infrastructure status, and model intelligence.**

PulseDeck runs on your Windows computer and brings together four independent modules:

| Module | First release |
| --- | --- |
| Codex | Local token/model/session history; no account-network queries |
| Claude Code | Local token/model/project history; subscription quotas when a capture is available |
| Isambard | Public service status and planned maintenance |
| Radar | Current community degradation scores, source test period, cached fallback |

## Start on Windows

Double-click **Start-PulseDeck.cmd**. It starts a hidden background process and opens your browser.
Starting it again opens the existing instance. Closing the browser leaves collection running.

- **Stop-PulseDeck.cmd** stops the background process.
- **Check-PulseDeck.cmd** shows read-only setup diagnostics.
- **Setup-Claude-Capture.cmd** installs the optional Claude Code quota capture, preserving an existing custom status line.

Python 3.10+ is required. The launcher detects Python on PATH, the Python launcher, or the Python runtime bundled with Codex. You can set `PULSEDECK_PYTHON` to an explicit executable. No pip packages or Node.js are needed to run the application.

```powershell
python -X utf8 -B -m pulsedeck launch
python -X utf8 -B -m pulsedeck check
python -X utf8 -B -m pulsedeck stop
```

Advanced: `python -X utf8 -B -m pulsedeck serve --port 8766 --sources all`.
The default port is 8765; if occupied, the application selects an available local port.

## Data sources and limitations

- **Codex:** reads local session metadata and the local thread database. Account network access is disabled in `pulsedeck/privacy.py`, including the app-server, legacy backend and Admin API paths. No cloud fallback is used.
- **Claude:** local JSONL history is independent of subscription quota capture. The official statusLine supplies quotas only when a compatible Claude Code client invokes it with those fields. Claude Desktop may write history without invoking the bridge. Missing or stale quotas stay visibly unavailable/stale; browser refresh cannot create a new account snapshot. This release does not automate a hidden Claude conversation or port the macOS expect refresher.
- **Isambard:** public service health and maintenance, not personal jobs or GPU allocations.
- **Radar:** community assessment scores, not official model ratings. HTML/catalog changes can require adapter updates; failed updates keep the last valid snapshot and its original timestamp.

Only usage metadata is displayed. Local token history is not a billing statement or a full account-wide total.

## Local storage

On Windows, runtime state and logs live under `%LOCALAPPDATA%\PulseDeck`.
Public caches live under `%LOCALAPPDATA%\PulseDeck\cache`.
The temporary browser access token stays in local runtime state and is never committed.

Supported overrides: `PULSEDECK_DATA_DIR`, `PULSEDECK_CACHE_DIR`, `CODEX_HOME`,
`CLAUDE_CONFIG_DIR`, `CLAUDE_BIN`, `CLAUDE_USAGE_SNAPSHOT`.
Legacy `CODEX_USAGE_CACHE_DIR` remains supported.

The server binds to loopback and requires a session capability for dashboard data.
GitHub synchronizes code and documentation, not credentials, conversation files, snapshots or logs.

## Architecture and next steps

`pulsedeck/modules.py` declares the four modules.
`pulsedeck/runtime.py` owns application lifecycle and local control.
Existing standalone collectors remain UI-independent and keep their regression tests.
The current browser is the first presentation layer; a tray/native window can reuse the runtime and collectors.

See [Windows development notes](docs/pulsedeck.md), [upstream dashboard API](WEB_DASHBOARD.md),
[Claude capture details](docs/claude-setup.md), and [Radar rules](docs/radar.md).
Some inherited documents and screenshots retain the original Codex-Usage name.

```powershell
python -X utf8 -B -m unittest discover -v
```

Node.js enables the JavaScript regression tests. CI installs it on Windows, Linux and macOS.

## Origin and license

Based on [Tyreal-Izual/Codex-Usage](https://github.com/Tyreal-Izual/Codex-Usage),
starting at commit `48fa74c`. Its Codex collection core derives from
[MacSteini/Codex-Usage](https://github.com/MacSteini/Codex-Usage).
The original history and both copyright notices are preserved in the [MIT license](LICENCE).

PulseDeck is independently maintained and is not an official OpenAI or Anthropic product.
