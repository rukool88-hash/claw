# 启动本地 faster-whisper 服务
# 用法： .\start.ps1
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

if (-not (Test-Path .\.venv)) {
    Write-Host "[whisper] creating venv..."
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\pip.exe install -r requirements.txt
}

$env:VAULT_HOST_ROOT = (Resolve-Path "$here\..\..").Path
$env:WHISPER_MODEL = $env:WHISPER_MODEL ?? "large-v3"
$env:WHISPER_DEVICE = $env:WHISPER_DEVICE ?? "auto"

Write-Host "[whisper] VAULT_HOST_ROOT=$env:VAULT_HOST_ROOT"
.\.venv\Scripts\uvicorn.exe server:app --host 0.0.0.0 --port 9000
