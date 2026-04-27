# 一次性把智谱 GLM-4.6 写入用户环境变量，供 Qwen Code（OpenAI 兼容协议）使用
# 用法： .\setup-zhipu.ps1 -ApiKey "<你的-智谱-Key>"
param(
    [Parameter(Mandatory = $true)]
    [string]$ApiKey,
    [string]$Model = "glm-4.6",
    [string]$BaseUrl = "https://open.bigmodel.cn/api/paas/v4"
)

# Qwen Code 读这三个变量
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $ApiKey, "User")
[Environment]::SetEnvironmentVariable("OPENAI_BASE_URL", $BaseUrl, "User")
[Environment]::SetEnvironmentVariable("OPENAI_MODEL", $Model, "User")

Write-Host "[OK] Qwen Code (OpenAI-compatible) env vars saved to USER scope."
Write-Host "    OPENAI_BASE_URL = $BaseUrl"
Write-Host "    OPENAI_MODEL    = $Model"
Write-Host ""
Write-Host "[!] 关闭并重新打开 PowerShell 让变量生效，然后运行: qwen" -ForegroundColor Yellow
