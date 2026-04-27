# Local faster-whisper service

长音频本地转写（短音频走 OpenAI Whisper API）。

## 一次性安装

```powershell
cd infra\whisper-local
.\start.ps1   # 首次会自动建 venv 并装依赖
```

依赖 NVIDIA GPU 驱动 + CUDA 12（faster-whisper 自带 CTranslate2）。无 GPU 会自动降级到 CPU `int8`。

## 运行
- 端口：`9000`
- 健康检查：`curl http://localhost:9000/health`
- n8n 容器内访问：`http://host.docker.internal:9000/transcribe`

## 注册为 Windows 开机自启（NSSM）

```powershell
# 下载 NSSM: https://nssm.cc/download
nssm install brain-vault-whisper "$PWD\.venv\Scripts\uvicorn.exe" "server:app --host 0.0.0.0 --port 9000"
nssm set brain-vault-whisper AppDirectory "$PWD"
nssm set brain-vault-whisper AppEnvironmentExtra "VAULT_HOST_ROOT=D:\VScode\机器人" "WHISPER_MODEL=large-v3"
nssm start brain-vault-whisper
```

## 环境变量
- `WHISPER_MODEL`：默认 `large-v3`（备选 `medium`、`small`，更快但略差）
- `WHISPER_DEVICE`：`auto` | `cuda` | `cpu`
- `WHISPER_COMPUTE_TYPE`：默认 `int8_float16`（GPU 用）
- `VAULT_HOST_ROOT`：把 n8n 传入的 `/vault/...` 映射到宿主机
