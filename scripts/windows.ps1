param(
    [ValidateSet('launch', 'stop', 'check', 'capture-claude')]
    [string]$Action = 'launch'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$candidates = @()
if ($env:PULSEDECK_PYTHON) { $candidates += $env:PULSEDECK_PYTHON }
foreach ($name in @('python', 'python3')) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if ($command -and $command.Source -notmatch '\\Microsoft\\WindowsApps\\') {
        $candidates += $command.Source
    }
}
$candidates += Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pythonLauncher) {
    $discovered = & $pythonLauncher.Source -3 -c 'import sys; print(sys.executable)' 2>$null
    if ($LASTEXITCODE -eq 0) { $candidates += $discovered }
}
$pythonPath = $null
foreach ($candidate in $candidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        & $candidate -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $pythonPath = $candidate; break }
    }
}
if (-not $pythonPath) {
    Write-Host 'Python 3.10+ was not found. Install Python, or set PULSEDECK_PYTHON to python.exe.'
    exit 1
}
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
Push-Location -LiteralPath $projectRoot
try {
    & $pythonPath -X utf8 -B -m pulsedeck $Action
    $result = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $result
