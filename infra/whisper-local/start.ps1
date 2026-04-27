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
if (-not $env:WHISPER_MODEL)  { $env:WHISPER_MODEL  = "large-v3" }
if (-not $env:WHISPER_DEVICE) { $env:WHISPER_DEVICE = "auto" }
# HuggingFace 在国内访问受限，使用镜像
if (-not $env:HF_ENDPOINT)    { $env:HF_ENDPOINT    = "https://hf-mirror.com" }
if (-not $env:HF_HUB_ENABLE_HF_TRANSFER) { $env:HF_HUB_ENABLE_HF_TRANSFER = "0" }

Write-Host "[whisper] VAULT_HOST_ROOT=$env:VAULT_HOST_ROOT"
.\.venv\Scripts\uvicorn.exe server:app --host 0.0.0.0 --port 9000
