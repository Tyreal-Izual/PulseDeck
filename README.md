# PulseDeck

> Current policy (0.4): Codex/Claude account collection is LOCAL ONLY. App-server, legacy backend and Admin API account requests are disabled. Claude snapshots are read from disk; no auth-status client is started. Isambard/Radar public fetches remain enabled. The disabled cloud adapters are retained only for possible future development.

**Your local dashboard for AI usage, infrastructure status, and model intelligence.**

PulseDeck runs on your Windows computer and brings together four independent modules:

| Module | First release |
| --- | --- |
| Codex | Local token/model/session history; no account-network queries |
| Claude Code | Local token/model/project history; subscription quotas when a capture is available |
| Isambard | Public service status and planned maintenance |
| Radar | Current community degradation scores, source test period, cached fallback |

## Windows desktop

Double-click **PulseDeck.exe** to open the standalone application window. Python
is included in the EXE; no terminal or separate browser is needed. Launching it
again activates the existing window. Closing the window stops its own backend.

Build from source with `Build-Desktop.ps1`; the result is `dist/PulseDeck.exe`.
Windows desktop builds are also produced by the **Windows desktop EXE** GitHub
Actions workflow. See [desktop build and runtime notes](docs/desktop.md).

The desktop window uses Microsoft Edge WebView2 Runtime, already present on
the development PC. It runs with normal user permissions.

## Browser / source entry

**Start-PulseDeck.cmd** opens the root desktop EXE when it exists. Otherwise it
uses the source browser entry. The browser entry starts a hidden backend;
closing that browser tab leaves the backend running.

- **Stop-PulseDeck.cmd** closes the desktop instance, or stops the legacy browser backend.
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

- **Codex:** reads local usage events and cumulative snapshots, attributing models from turn context. Account network access is disabled in `pulsedeck/privacy.py`, including the app-server, legacy backend and Admin API paths. No cloud fallback is used.
- **Claude:** local JSONL history is independent of subscription quota capture. The official statusLine supplies quotas only when a compatible Claude Code client invokes it with those fields. Claude Desktop may write history without invoking the bridge. Missing or stale quotas stay visibly unavailable/stale; browser refresh cannot create a new account snapshot. This release does not automate a hidden Claude conversation or port the macOS expect refresher.
- **Isambard:** public service health and maintenance, not personal jobs or GPU allocations.
- **Radar:** community assessment scores, not official model ratings. HTML/catalog changes can require adapter updates; failed updates keep the last valid snapshot and its original timestamp.

Only usage metadata is displayed. Local token history is not a billing statement or a full account-wide total.

## Usage views

Choose **Today / Last 7 days / Last 30 days / All local history**. Totals,
models, projects, sessions, and charts share the same local calendar range.
The overview has two usage cards; quota capture and Radar details are collapsed.
Unchanged logs require no content reads; appends read only the suffix and small
hash anchors. The index stays in memory. See [accounting and limitations](docs/local-usage.md).

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
The desktop window and browser entry share the same collectors. Desktop lifecycle
and window activation live in `pulsedeck/desktop.py`.

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
