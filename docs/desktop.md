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
`%LOCALAPPDATA%\PulseDeck\desktop`. The desktop backend normally uses port 8766
and chooses a free port if it is occupied. The older browser/CLI entry remains
available for development, using separate session state.

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
personal history. Source tests cover lifecycle ownership and navigation policy.

## Packaging

The single-file package uses pywebview with EdgeChromium and PyInstaller's
windowed bootloader. It unpacks its bundled runtime at startup; application
preferences remain in AppData. Third-party package metadata/licenses and the
Python runtime license are included when available. No Qt/CEF engine is bundled.

References: [pywebview packaging](https://pywebview.flowrl.com/guide/freezing.html),
[Windows engine requirements](https://pywebview.flowrl.com/guide/web_engine.html).
