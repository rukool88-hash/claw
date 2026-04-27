# 每天 22:00 自动跑 qwen /maintain
$ErrorActionPreference = "Continue"
Set-Location "D:\VScode\机器人"
$logDir = ".qwen"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir "maintain.log"
"`n===== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') /maintain start =====" | Out-File -FilePath $logFile -Append -Encoding utf8
& qwen -p "/maintain" *>> $logFile
"===== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') /maintain end (exit=$LASTEXITCODE) =====" | Out-File -FilePath $logFile -Append -Encoding utf8
