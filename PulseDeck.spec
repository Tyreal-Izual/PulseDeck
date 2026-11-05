# Build in an isolated environment: see Build-Desktop.ps1.
from pathlib import Path
import sys
import ssl
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

root = Path(SPECPATH)
licenses = []
for package in ("pywebview", "pythonnet", "clr_loader", "bottle", "proxy_tools", "cffi",
                "pycparser", "typing_extensions", "pyinstaller"):
    licenses += copy_metadata(package)
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.exists():
    licenses.append((str(python_license), "licenses/python"))
# Some bundled Python distributions load this trust-policy resource from ssl.py.
# Preserve that policy in frozen builds instead of changing TLS verification.
ssl_policy = Path(ssl.__file__).with_name("codex-rejected-cas.pem")
if ssl_policy.exists():
    licenses.append((str(ssl_policy), "."))
a = Analysis(
    [str(root / "desktop_entry.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "templates"), "templates"),
        (str(root / "static"), "static"),
        (str(root / "assets" / "pulsedeck.ico"), "assets"),
        (str(root / "LICENCE"), "."),
    ] + collect_data_files("webview") + licenses,
    hiddenimports=["webview.platforms.winforms", "webview.platforms.edgechromium", "clr"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "cefpython3",
              "webview.platforms.gtk", "webview.platforms.cocoa", "webview.platforms.qt",
              "webview.platforms.android", "webview.platforms.cef"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="PulseDeck",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(root / "assets" / "pulsedeck.ico"),
)
