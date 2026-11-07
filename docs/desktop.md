# PulseDeck desktop

Double-click `PulseDeck.exe` to open the standalone Windows window. It includes
Python and its application dependencies. Windows needs .NET Framework 4.6.2+
and Microsoft Edge WebView2 Runtime; both were available on the development PC.
No terminal, separate browser, or administrator permission is needed.

The existing local dashboard is rendered inside the application window. Its
authenticated loopback backend runs in the same application process. Closing
the window stops that backend. A second launch activates the existing window.
An explicitly clicked external source link can open the default browser.
On opening the overview, the page scrolls to Codex quota as soon as local data
arrives, adjusting if the remaining initial content changes the available page
height. Scrolling manually cancels this; later refreshes do not move the view
back. An explicit Radar link keeps its own target.

Tokens and quota windows remain local; Reset Credits alone use a cached read-only
Codex account lookup. Isambard and Radar still fetch public
information. Version 0.4 uses [event accounting and unified time ranges](local-usage.md).

Runtime state, bounded error logs, and WebView preferences live under
`%LOCALAPPDATA%\PulseDeck\desktop`. The desktop backend normally uses port 8766;
the browser entry uses 8765. If its default port is unavailable, it retries once
with port 0 so Windows selects a free port, and records that actual port in the
session state. Nondefault fixed ports and unrelated startup errors still fail.

Windows listeners use `SO_EXCLUSIVEADDRUSE` before binding, with address/port
sharing disabled. Both address-in-use errors and Windows `EACCES` / Winsock
10013 and 10048 trigger default-port fallback. This covers occupied or excluded
ports without joining another process's listener. POSIX retains address reuse
for normal restarts, but never enables `SO_REUSEPORT`.
See [Microsoft's socket binding documentation](https://learn.microsoft.com/en-us/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse).
The older browser/CLI entry remains available for development, using separate
session state.

## Build

On Windows with Python 3.12:

```powershell
./Build-Desktop.ps1 -Python C:\path\python.exe
```

The build uses `.venv-desktop` and produces `dist/PulseDeck.exe`. Copy that EXE
to the project root or another convenient location. `Start-PulseDeck.cmd`
prefers the root EXE when it exists. Executables and build caches are not
committed to Git.

```powershell
./Build-Desktop.ps1 -SkipInstall
./dist/PulseDeck.exe --self-check .local/desktop-check.json
```

The packaged self-check tests included assets, the .NET bridge, authenticated
activation and backend shutdown. It does not query account services or collect
personal history. Its JSON reports the general account-network flag and the
Reset Credits exception separately. Source tests cover lifecycle ownership and navigation policy.

## Packaging

The single-file package uses pywebview with EdgeChromium and PyInstaller's
windowed bootloader. It unpacks its bundled runtime at startup; application
preferences remain in AppData. Third-party package metadata/licenses and the
Python runtime license are included when available. No Qt/CEF engine is bundled.

References: [pywebview packaging](https://pywebview.flowrl.com/guide/freezing.html),
[Windows engine requirements](https://pywebview.flowrl.com/guide/web_engine.html).
