@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows.ps1" -Action stop
if errorlevel 1 pause
