# Hermes Agent — 迁移配置（完整版）

> 把原 Qwen Code + n8n（WF1/WF2/WF4）+ Windows schtasks 的 PKM 自动化栈，
> 全部收敛到 **Hermes Agent v0.11.0** 跑在 `ubuntu24` Docker 容器内。

## 当前架构

```
Telegram(@calooabot) ─┐
QQBot ─────────────── ├─→ ubuntu24 容器 ─→ Hermes Gateway (root)
RSS publisher ───────┘     │
HTTP POST :8644            ├─→ GLM-4.6 (open.bigmodel.cn)
                           ├─→ /workspace (Vault, mount)
                           └─→ pkm-vault skill
                                ├ /maintain  (cron 22:00)
                                ├ /ideate
                                ├ /debate
                                └ /draft

宿主机端口:
  2222 → 22    (SSH)
  8644 → 8644  (Webhook 收 RSS)
  8010 → 8000  (Hermes API server)
```

## 关键映射

| 原组件 | 现位置 | 状态 |
|---|---|---|
| Qwen Code CLI | `hermes -z` / `hermes chat` | ✓ |
| `.qwen/commands/*.md` | [skills/pkm-vault/SKILL.md](skills/pkm-vault/SKILL.md) | ✓ |
| `CLAUDE.md` 宪法 | cron `--workdir /workspace` 自动注入 | ✓ |
| 人格 / SOUL | [SOUL.md](SOUL.md) | ✓ |
| n8n WF1（Telegram 语音） | Hermes Telegram gateway（builtin STT） | ✓ ¹ |
| n8n WF4（22:00 通知） | `hermes cron pkm-maintain` | ✓ |
| n8n WF2（RSS webhook） | `hermes webhook /webhooks/rss-ingest` | ✓ |
| Windows schtasks `brain-vault-maintain` | 同 cron | ✓（已 Disable）|
| Whisper service `host.docker.internal:9000` | Hermes builtin local STT | ✓（仍可独立运行）|

¹ 见下方"语音处理说明"。

## 文件清单

| 文件 | 用途 |
|---|---|
| [skills/pkm-vault/SKILL.md](skills/pkm-vault/SKILL.md) | 4 个核心命令的执行规则 |
| [SOUL.md](SOUL.md) | Hermes 人格设定，含语音/链接默认归档规则 |
| [create_cron.py](create_cron.py) | 用内部 API 创建 daily 22:00 cron（绕过 CLI bug） |
| [setup_webhook.py](setup_webhook.py) | 启用 webhook 平台 + 创建 `rss-ingest` 订阅 |
| [recover.sh](recover.sh) / [recover.ps1](recover.ps1) | **灾难恢复**脚本：在新装 Hermes 上一键还原全部配置 |
| [setup-cron.sh](setup-cron.sh) | bash 等价物（已知有 CLI bug，仅留作记录） |
| [../ubuntu24/start-hermes-stack.sh](../ubuntu24/start-hermes-stack.sh) | 容器 CMD：后台起 gateway + 前台 sshd |
| [../ubuntu24/Dockerfile.hermes](../ubuntu24/Dockerfile.hermes) | 把 Hermes 安装快照固化为 `hermes-v2` 镜像 |

## 一次性安装流程（首次或灾难恢复）

```powershell
# 1. 容器跑起来（如果还没起）
docker run -d --name ubuntu24 --restart unless-stopped `
  -p 2222:22 -p 8644:8644 -p 8010:8000 `
  -v "D:\VScode\机器人:/workspace" `
  --add-host=host.docker.internal:host-gateway `
  ubuntu24-dev:latest

# 2. 进容器装 Hermes（用户提供的安装脚本）
docker exec -it ubuntu24 bash
#   (in container) 跑你的 Hermes 安装命令，例如：
#     curl -fsSL https://hermes-agent.nousresearch.com/install.sh | sh
#   或 pip install / git clone …（按你之前的方式）

# 3. 配 Telegram + QQBot pairing（必须 TTY）
docker exec -it ubuntu24 hermes setup

# 4. 一键还原 PKM 配置（GLM key、skill、SOUL、cron、webhook）
./infra/hermes/recover.ps1

# 5. 把 Hermes 安装固化为 v2 镜像（自动启动 gateway）
docker commit ubuntu24 ubuntu24-dev:hermes-snapshot
docker build -t ubuntu24-dev:hermes-v2 -f infra/ubuntu24/Dockerfile.hermes infra/ubuntu24
docker stop ubuntu24; docker rm ubuntu24
docker run -d --name ubuntu24 --restart unless-stopped `
  -p 2222:22 -p 8644:8644 -p 8010:8000 `
  -v "D:\VScode\机器人:/workspace" `
  --add-host=host.docker.internal:host-gateway `
  ubuntu24-dev:hermes-v2
```

之后每次 Docker / 主机重启，gateway 自动起来。

## 验证清单

```powershell
docker exec ubuntu24 hermes status
# 期望：Model glm-4.6, Provider Z.AI/GLM, Telegram ✓, QQBot ✓, Webhook ✓, Gateway running

docker exec ubuntu24 hermes cron list
# 期望：pkm-maintain, schedule '0 22 * * *', deliver telegram

docker exec ubuntu24 hermes webhook list
# 期望：rss-ingest, /webhooks/rss-ingest

docker exec ubuntu24 hermes -z "你好" --yolo   # 验证 GLM 通路
```

## 语音处理说明

Hermes 的 Telegram 适配器收到语音消息会**自动用 builtin local Whisper 转写**，
然后把转写文本作为 LLM 输入。SOUL.md 已写入硬指令：**"语音消息一律先归档到
`/workspace/inbox/transcripts/<timestamp>-tg<msg_id>.md`，再回一句 ✓"**。

> 如果发现 LLM 没遵守归档指令，备用方案是关掉 Hermes 的 Telegram 适配器，
> 重新启用 n8n WF1（直接 Telegram polling → Whisper HTTP → 文件，零 LLM 成本）。
> 不能两边同时 polling，否则消息互抢。

`infra/whisper-local/` 的 9000 端口 Whisper 服务**保留**，可作为外部转写回退。

## 已知坑（务必记住）

1. **`hermes cron create "0 22 * * *" "<prompt>"` 失败**：当 schedule 含空格时
   argparse 把 prompt 当作 unknown args。解决：用 [create_cron.py](create_cron.py)
   直接调内部 API。
2. **dev 用户读不到 venv**：`Permission denied` on
   `/usr/local/lib/hermes-agent/venv/bin/python3`。Hermes 必须以 **root** 运行
   （`docker exec ubuntu24 …`，不要加 `-u dev`）。
3. **PowerShell 写 `docker commit --change='CMD ["..."]'` 危险**：JSON 数组形式
   会被 shell 当字符串保留方括号，导致镜像 CMD 损坏。**永远用 Dockerfile** 而非
   `commit --change` 设置 CMD。[Dockerfile.hermes](../ubuntu24/Dockerfile.hermes)
   就是为此而生。
4. **删除容器前先 commit**：`/root/.hermes` 是容器 fs 不在 volume 里，
   `docker rm` 一执行，所有 pairing / auth / 状态库丢失。本仓库历史上踩过此坑
   （2026-04-28）。

## 容器与认证

- 容器：`ubuntu24`（Ubuntu 24.04），SSH `localhost:2222`
- 用户：`dev`/`dev123456`（sudo NOPASSWD），**root 密码 `dev123456`**
- 必须以 root 操作 Hermes（dev 无 venv 权限）
- 重启策略：`unless-stopped`

## n8n 现状

容器 `n8n` 仍在 5678 端口运行，但 WF1/WF2/WF4 全部 `active=false`。归档资源，
不再使用。如果完全不需要可以 `docker stop n8n` 节省资源。

## 仓库

- GitHub: `rukool88-hash/claw`，分支 `main`
- 本目录所有改动每次任务后自动 commit + push
