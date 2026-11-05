# PulseDeck 0.1 development

## Boundaries

- `pulsedeck/modules.py`: module catalog, data kinds, report identifiers and refresh policies.
- `pulsedeck/codex_rpc.py`: bounded read-only app-server protocol, cached for 60 seconds.
- `pulsedeck/runtime.py`: loopback server lifecycle, authenticated control, OS single-instance lock.
- `pulsedeck/__main__.py`: browser launcher, background process, diagnostics and stop commands.
- Existing root collectors: metadata extraction, source caches, normalization, reports.
- `templates/` and `static/`: current browser presentation.
- `scripts/windows.ps1`: Python discovery and UTF-8 startup.

A desktop shell can replace browser opening while preserving Runtime and the collectors.
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
and missing or stale Claude quotas.

## Planned later

Tray/native presentation, configurable modules, notification thresholds,
and optional personal Isambard/Slurm job monitoring.
Automatic Claude quota refresh while no compatible client is active is not implemented.
