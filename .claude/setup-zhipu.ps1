# 一次性把智谱 GLM-4.6 配置写入当前用户环境变量
# 用法： .\setup-zhipu.ps1 -ApiKey "<你的-智谱-Key>"
param(
    [Parameter(Mandatory = $true)]
    [string]$ApiKey,
    [string]$Model = "glm-4.6",
    [string]$SmallModel = "glm-4.5-air",
    [string]$BaseUrl = "https://open.bigmodel.cn/api/anthropic"
)

[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", $BaseUrl, "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", $ApiKey, "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_MODEL", $Model, "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_DEFAULT_HAIKU_MODEL", $SmallModel, "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_SMALL_FAST_MODEL", $SmallModel, "User")

Write-Host "[OK] Anthropic-compatible env vars (Zhipu GLM) saved to USER scope."
Write-Host "    BASE_URL = $BaseUrl"
Write-Host "    MODEL    = $Model"
Write-Host "    SMALL    = $SmallModel"
Write-Host ""
Write-Host "[!] 关闭并重新打开 PowerShell 让变量生效，然后运行: claude" -ForegroundColor Yellow
