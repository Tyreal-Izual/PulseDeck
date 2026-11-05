@echo off
if exist "%~dp0PulseDeck.exe" (
    start "" "%~dp0PulseDeck.exe"
    exit /b
)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows.ps1" -Action launch
if errorlevel 1 pause
