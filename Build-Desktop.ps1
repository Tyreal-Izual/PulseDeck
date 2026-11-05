param([string]$Python, [switch]$SkipInstall)
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
if(-not $Python){
    $command=Get-Command python -ErrorAction SilentlyContinue
    if($command -and $command.Source -notmatch '\\Microsoft\\WindowsApps\\'){$Python=$command.Source}
}
if(-not $Python){
    $candidate=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if(Test-Path -LiteralPath $candidate){$Python=$candidate}
}
if(-not $Python){throw 'Pass -Python with the path to a Python 3.12+ interpreter.'}
$venv=Join-Path $root '.venv-desktop\Scripts\python.exe'
if(-not (Test-Path -LiteralPath $venv)){
    & $Python -m venv (Join-Path $root '.venv-desktop')
    if($LASTEXITCODE -ne 0){throw 'Unable to create the isolated build environment.'}
}
Push-Location -LiteralPath $root
try{
    if(-not $SkipInstall){
        $savedConfig=$env:PIP_CONFIG_FILE
        try{
            $env:PIP_CONFIG_FILE='nul'
            & $venv -m pip install --index-url https://pypi.org/simple -r requirements-desktop.txt
            if($LASTEXITCODE -ne 0){throw 'Desktop build dependencies could not be installed.'}
        }finally{$env:PIP_CONFIG_FILE=$savedConfig}
    }
    & $venv -m PyInstaller --noconfirm PulseDeck.spec
    if($LASTEXITCODE -ne 0){throw 'Desktop packaging failed.'}
    Write-Host "Desktop EXE: $(Join-Path $root 'dist\PulseDeck.exe')"
}finally{Pop-Location}
