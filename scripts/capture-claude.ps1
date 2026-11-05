param([Parameter(Mandatory=$true)][string]$Python)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$payload = [Console]::In.ReadToEnd()
$scriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'claude_usage_statusline.py'
$payload | & $Python -X utf8 -B $scriptPath
exit $LASTEXITCODE
