# PulseDeck development

> Current policy: Codex/Claude account collection is LOCAL ONLY. App-server, legacy backend and Admin API account requests are disabled. Claude snapshots are read from disk; no auth-status client is started. Isambard/Radar public fetches remain enabled. Earlier cloud-adapter notes below are historical and inactive.

## Boundaries

- `pulsedeck/modules.py`: module catalog, data kinds, report identifiers and refresh policies.
- `pulsedeck/privacy.py`: disables all account-network collection.
- `pulsedeck/codex_rpc.py`: inactive app-server adapter; blocked by the local-only policy.
- `pulsedeck/runtime.py`: loopback server lifecycle, authenticated control, OS single-instance lock.
- `pulsedeck/__main__.py`: browser launcher, background process, diagnostics and stop commands.
- Existing root collectors: metadata extraction, source caches, normalization, reports.
- `templates/` and `static/`: current browser presentation.
- `scripts/windows.ps1`: Python discovery and UTF-8 startup.

The Windows desktop shell uses the same Runtime and collectors as the browser entry.
Do not couple local file parsing or account authentication to a particular UI toolkit.

## API

The inherited authenticated APIs remain unchanged:
`/api/usage?report=...`, `/api/codex-radar`, and `/api/sources`.

`GET /api/pulsedeck` returns application version and the enabled module catalog.
This is runtime health, not a claim that every source has fresh data.
`POST /api/pulsedeck/stop` requires the session capability and `X-PulseDeck-Action: stop`.

## Verification

Run `python -X utf8 -B -m unittest discover -v`.
Tests use synthetic data, local temporary files and loopback servers.
Real-data smoke checks must report unavailable sources without replacing them with mock data.
For UI checks verify English/Chinese, desktop/mobile widths, no horizontal overflow,
and missing or stale Claude quotas. Codex and Claude quota panels each occupy a full row.

Tests follow maintained behavior. The inactive Claude auth-client implementation
and its login-indicator/string-matching tests have been removed. Progressive UI
tests exercise local usage and public Isambard requests; they no longer simulate
account endpoints. Keep the local-only transport guards, quota parsing/countdown,
incremental accounting, and runtime lifecycle regressions. Optional CLI adapters
and their tests remain separate from the current dashboard.

The old Radar IQ/cost composite and RadarBench adapters are retired. Tests cover
only the current degradation source, plus rejection/recovery of old cache formats.
Shared file-index append/truncate/replacement tests live in `test_local_usage.py`;
collector tests retain their report-shape and CLI/export responsibilities.

## Planned later

Tray/native presentation, configurable modules, notification thresholds,
and optional personal Isambard/Slurm job monitoring.
Automatic Claude quota refresh while no compatible client is active is not implemented.
