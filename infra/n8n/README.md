# n8n — 自动化处理层

## 启动

```powershell
cd infra\n8n
copy .env.example .env
# 编辑 .env 改密码
docker compose up -d
```

访问 <http://localhost:5678>，使用 .env 中的账号密码登录。

## 容器内路径
- Vault 挂载点：`/vault`（对应宿主机仓库根目录）
- n8n 节点写文件时使用 `/vault/inbox/transcripts/...`

## 调用本地 faster-whisper
HTTP Request 节点 URL：`http://host.docker.internal:9000/transcribe`

## 4 个核心工作流（导入后配置）
见仓库根目录 [DEPLOY.md](../../DEPLOY.md) 第 4 节。
工作流 JSON 模板待首次使用时在 n8n UI 中创建并导出到 [workflows/](workflows/) 目录。
