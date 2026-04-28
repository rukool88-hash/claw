# Hermes Agent — 迁移配置

> 这一目录是把原先 Qwen Code + n8n 多工作流栈迁移到 **Hermes Agent v0.11.0** (容器 `ubuntu24`) 的全部配置。

## 运行环境

| 项 | 值 |
|---|---|
| 容器 | `ubuntu24` (Ubuntu 24.04) |
| Hermes 路径 | `/usr/local/lib/hermes-agent`（root 拥有，必须以 root 操作）|
| Hermes home | `/root/.hermes/` |
| LLM | **GLM-4.6** via `https://open.bigmodel.cn/api/paas/v4` |
| Vault 挂载 | `D:\VScode\机器人` ↔ `/workspace`（包含 `CLAUDE.md`，cron 自动注入）|
| 通讯平台 | Telegram（@calooabot，polling）+ QQBot |

## 已迁移项

| 来源 | 迁移到 | 状态 |
|---|---|---|
| Qwen Code CLI | `hermes -z` / `hermes chat` | ✓ |
| `.qwen/commands/{maintain,ideate,debate,draft}.md` | `~/.hermes/skills/pkm-vault/SKILL.md` | ✓ |
| `CLAUDE.md` 宪法 | cron `--workdir /workspace` 自动注入 | ✓ |
| n8n WF1（Telegram 语音 polling） | Hermes Telegram gateway | ✓（n8n WF1 已停用避免冲突）|
| n8n WF4（22:00 通知） | `hermes cron pkm-maintain` | ✓（n8n WF4 已停用）|
| Windows 计划任务 `brain-vault-maintain` | 同上 | ✓（已 Disable）|
| n8n WF2（RSS webhook） | 暂未迁移，已停用 | ⏸ 后续可用 `hermes webhook` 重建 |

## 关键文件

- [skills/pkm-vault/SKILL.md](skills/pkm-vault/SKILL.md) — 4 个核心命令的执行规则（容器内拷贝到 `~/.hermes/skills/pkm-vault/`）
- [create_cron.py](create_cron.py) — 用 Hermes 内部 API 创建 cron（绕过 CLI argparse 在带空格 schedule + prompt 时的解析 bug）
- [setup-cron.sh](setup-cron.sh) — bash 等价物（注：受 hermes CLI bug 影响，仅供参考）

## 重建步骤（灾难恢复）

```bash
# 0. 进容器
docker exec -it ubuntu24 bash

# 1. 配置 GLM key（写入 ~/.hermes/.env）
sed -i 's|^# GLM_API_KEY=.*|GLM_API_KEY=<KEY>|' ~/.hermes/.env
sed -i 's|^# GLM_BASE_URL=.*|GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4|' ~/.hermes/.env

# 2. 配置默认模型
hermes config set model.default glm-4.6
hermes config set model.provider glm
hermes config set model.base_url https://open.bigmodel.cn/api/paas/v4

# 3. 安装 PKM skill
mkdir -p ~/.hermes/skills/pkm-vault
cp /workspace/infra/hermes/skills/pkm-vault/SKILL.md ~/.hermes/skills/pkm-vault/

# 4. 创建 cron（必须用 Python API）
/usr/local/lib/hermes-agent/venv/bin/python3 /workspace/infra/hermes/create_cron.py

# 5. 重启 gateway
pkill -f 'hermes gateway run' || true
nohup hermes gateway run > ~/.hermes/logs/gateway.log 2>&1 < /dev/null & disown

# 6. 验证
hermes status
hermes cron list
```

## 已知问题

- `hermes cron create` CLI 在 schedule 含空格（cron 表达式如 `"0 22 * * *"`）时无法接收 prompt — 已通过 [create_cron.py](create_cron.py) 直接调内部 API 绕过。
- dev user 无法读取 venv（权限拒绝）—— Hermes 必须以 root 操作。
