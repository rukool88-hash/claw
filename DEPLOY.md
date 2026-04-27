# DEPLOY.md — 完整部署清单

> 跟着这份清单按顺序执行，**每完成一节做对应"验证"再进下一节**。

---

## 0. 前置依赖（一次性安装）

按顺序在 PowerShell（管理员）中执行：

```powershell
# 0.1 包管理器（如未安装 winget 跳过）
winget install --id Git.Git -e
winget install --id GitHub.cli -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Python.Python.3.11 -e
winget install --id Docker.DockerDesktop -e
winget install --id Obsidian.Obsidian -e

# 0.2 验证
git --version
gh --version
node -v          # 应 >= 20
python --version # 应是 3.11.x
docker --version
```

> 安装 Docker Desktop 后请重启并启用 **WSL2 后端**。

### API Key 准备（中国大陆方案）
> Anthropic / OpenAI 在中国大陆无法直接访问，因此用以下兼容端替代：
- [ ] **智谱 BigModel API Key**（<https://open.bigmodel.cn>）→ 充值后开通 **GLM Coding Plan**，会得到一个 Anthropic 兼容端点
- [ ] Telegram Bot Token（在 @BotFather 创建）
- [ ] Readwise / Inoreader 账号（可选，先跳过）
- [ ] GitHub 账号（可选 `gh auth login`，本仓库已推送）

> 语音转写不再使用 OpenAI Whisper API，全部走 **本地 faster-whisper**（见第 5 节）。

---

## 1. 第三层：Vault + GitHub 同步

```powershell
cd D:\VScode\机器人

# 初始化 Git（如果还没）
git init -b main
git add .
git commit -m "chore: bootstrap brain-vault skeleton"

# 创建 GitHub 私有仓库并推送
gh repo create brain-vault --private --source . --remote origin --push
```

### Obsidian 配置
1. 打开 Obsidian → "Open folder as vault" → 选 `D:\VScode\机器人`。
2. 设置 → Community plugins → 关闭 Restricted mode → 安装：
   - **Obsidian Git**（自动 commit/push）
   - **Templater**
   - **Dataview**
   - **QuickAdd**
3. Obsidian Git 设置：
   - `Vault backup interval (minutes)`：`10`
   - `Auto pull interval (minutes)`：`10`
   - `Commit message`：`vault: auto {{date}}`

### ✅ 验证
- 在 Obsidian 编辑 [inbox/ideas.md](inbox/ideas.md) 加一行 → 等 10 分钟，GitHub 出现新 commit。

---

## 2. 第四层：Claude Code AI 引擎（接智谱 GLM-4.6）

### 2.1 安装 Claude Code CLI
```powershell
npm install -g @anthropic-ai/claude-code
```

### 2.2 配置环境变量指向智谱兼容端点
智谱 BigModel 提供与 Anthropic 完全兼容的 `/api/anthropic` 端点，Claude Code 只需切换 `ANTHROPIC_BASE_URL` 即可。

**永久写入用户环境变量**（PowerShell 管理员）：
```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://open.bigmodel.cn/api/anthropic", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", "<你的智谱-API-Key>", "User")
# 模型映射（智谱 Coding Plan 推荐）
[Environment]::SetEnvironmentVariable("ANTHROPIC_MODEL", "glm-4.6", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_DEFAULT_HAIKU_MODEL", "glm-4.5-air", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_SMALL_FAST_MODEL", "glm-4.5-air", "User")
```
关闭并重开 PowerShell 让变量生效。

> 备注：环境变量优先级高于 `claude` 自身配置，**不要** 在 `claude` 里再走 Anthropic 登录流程，直接跳过即可。

### 2.3 在 Vault 根目录启动
```powershell
cd D:\VScode\机器人
claude --dangerously-skip-permissions   # 首次跳过权限确认；后续可去掉此参数
```

它会自动加载 [CLAUDE.md](CLAUDE.md) 和 [.claude/settings.json](.claude/settings.json)。

### 2.4 验证
- `claude` 启动后输入 `/` 能补全 `/maintain` `/ideate` `/debate` `/draft` 4 个命令。
- 输入 `你好，列出本仓库的 5 大目录` 看是否有响应（说明 GLM-4.6 通了）。

> 如果回复 `401/403`：检查 ANTHROPIC_AUTH_TOKEN；
> 如果 `model not found`：把 `ANTHROPIC_MODEL` 换成你套餐内允许的名字（如 `glm-4.6`、`glm-4-plus`）。

### ✅ 验证
- 在 [inbox/transcripts/](inbox/transcripts/) 放一个测试 `.md`（任意一段话）。
- 运行 `/maintain --dry-run`，应列出该文件并给出处理计划。
- 运行 `/maintain`，应在 [knowledge/](knowledge/) 出现新卡片，原文件移到 `inbox/transcripts/_processed/`。

---

## 3. 第二层：n8n（Docker）

```powershell
cd D:\VScode\机器人\infra\n8n
copy .env.example .env
notepad .env   # 改强密码
docker compose up -d
docker compose logs -f n8n   # 看到 "Editor is now accessible" 即可 Ctrl+C
```

打开 <http://localhost:5678>，用 .env 里的账号密码登录。

### 配置凭证（Credentials）
在 n8n 左下角 → Credentials → New：
- **HTTP Header Auth**（命名 `Zhipu`）：Header 名 `Authorization`，值 `Bearer <你的智谱-API-Key>`（用于在 n8n 里调 GLM）
- **Telegram**：粘贴 Bot Token
- （后续按需）Readwise / Inoreader / IMAP

> 不需要配置 OpenAI / Anthropic 凭证。

### ✅ 验证
- n8n 中创建一个 Manual Trigger → Write Binary File 节点 → 路径 `/vault/inbox/transcripts/test-from-n8n.md` → 内容随意 → Execute。
- 宿主机的 `inbox/transcripts/test-from-n8n.md` 应出现。

---

## 4. 4 个核心工作流（在 n8n UI 创建并保存）

> 每个工作流创建完后导出 JSON 到 [infra/n8n/workflows/](infra/n8n/workflows/) 提交入库。

### WF1 — 手机录音 → 转写（全部走本地 faster-whisper）
节点链：
1. **Telegram Trigger**（事件：`message`，含 voice/audio）
2. **Telegram → Get File**（下载到 binary）
3. **Write Binary File**：`/vault/inbox/audio/{{ $now.format('yyyyMMdd-HHmmss') }}-{{$json.message.message_id}}.ogg`
4. **HTTP Request** → `POST http://host.docker.internal:9000/transcribe`
   - Body (JSON)：`{"path":"/vault/inbox/audio/<上一步文件名>","language":"zh"}`
   - 不再判断时长，长短音频统一本地处理；本地服务首次启动会自动下载 `large-v3` 模型（~3GB）。
5. **Set**：拼接 markdown：
   ```
   ---
   created: {{ $now.toISO() }}
   type: transcript
   source: telegram
   duration: {{ $json.duration }}
   ---

   # {{ $now.format('yyyy-MM-dd HH:mm') }} 录音

   {{ $json.text }}
   ```
6. **Write File** → `/vault/inbox/transcripts/{{ $now.format('yyyyMMdd-HHmm') }}.md`

### WF2 — RSS / 标星 → Vault
1. **Inoreader Trigger**（或 Webhook + IFTTT/Inoreader Rules）
2. **Set**：构造一行 `- [{{title}}]({{url}}) — {{summary}}`
3. **Read/Write File**（追加模式）→ `/vault/inbox/rss/{{ $now.format('yyyy-MM-dd') }}.md`

### WF3 — 邮件摘录
1. **IMAP Email Trigger**（过滤 label `vault`）
2. **HTML to Markdown**
3. **Write File** → `/vault/inbox/rss/email-{{ $now.format('yyyyMMdd-HHmm') }}.md`

### WF4 — 每天 22:00 自动 /maintain
1. **Schedule Trigger**（Cron `0 22 * * *`）
2. **Execute Command**（需在 docker-compose 中设 `N8N_RUNNERS_ENABLED=true`、并为 n8n 容器提供 PowerShell 访问）。实践中更推荐：**不从容器里跳出去**，改用宿主机任务调度：
   - **方案 A（推荐）**：用 Windows 任务计划程序直接跳过 n8n：
     ```powershell
     # 一次性创建任务（管理员 PowerShell）
     $cmd = 'cd D:\VScode\机器人; claude --dangerously-skip-permissions -p "/maintain" >> D:\VScode\机器人\.claude\maintain.log 2>&1'
     schtasks /Create /SC DAILY /ST 22:00 /TN "brain-vault-maintain" /TR "powershell -NoProfile -Command ""$cmd""" /F
     ```
   - **方案 B**：仍由 n8n Schedule 起始 → webhook 回调宿主机上一个小服务起 `claude -p "/maintain"`。
3. （可选）**失败 Telegram 通知**。

### ✅ 验证
- Telegram 发 30 秒语音 → 2 分钟内出现 [inbox/transcripts/](inbox/transcripts/) 新文件。
- 等 22:00（或临时改 cron 到几分钟后）→ 自动 `/maintain` 跑通。

---

## 5. 第五层：本地 faster-whisper

```powershell
cd D:\VScode\机器人\infra\whisper-local
.\start.ps1
```

首次会创建 venv + 安装依赖（large-v3 模型 ~3GB，会下载）。

### 注册为开机自启（推荐）
见 [infra/whisper-local/README.md](infra/whisper-local/README.md) 中 NSSM 段。

### ✅ 验证
```powershell
curl http://localhost:9000/health
# 放一段 mp3 到 inbox/audio/test.mp3 后
curl -X POST http://localhost:9000/transcribe `
  -H "Content-Type: application/json" `
  -d '{\"path\":\"/vault/inbox/audio/test.mp3\",\"language\":\"zh\"}'
```

---

## 6. 第一层：捕获通道

| 通道 | 配置 |
|---|---|
| 手机语音 | Telegram → 你的 Bot 直接发语音（WF1 自动处理） |
| RSS | Inoreader 订阅源 → Rules → 标星即 webhook 到 n8n（WF2） |
| 书摘 | Readwise 接 Kindle / 微信读书 → Readwise webhook → n8n |
| 会议录音 | OBS 录音 → 保存到 `D:\VScode\机器人\inbox\audio\` → WF1 文件监听分支（可加一个 Local File Trigger） |

---

## 7. 第五层：输出层

模板已经在 [output/](output/) 4 个子目录留好。`/draft` 命令会按 type 自动选模板。

如果未来要自动发布到博客：
- 在 GitHub repo Actions 加 `articles/` push 触发 → 校验 frontmatter `status: published` → 同步到 Hexo/Hugo/Notion。MVP 先不上。

---

## 端到端冒烟测试（按顺序，全部通过即上线）

- [ ] `docker ps` 看到 `n8n` 运行
- [ ] `curl http://localhost:9000/health` 返回 ok
- [ ] `claude --version` 成功
- [ ] Obsidian 改文件 → 10 分钟内 GitHub 出现 commit
- [ ] Telegram 发语音 → `inbox/transcripts/` 出现 .md
- [ ] 放 ≥10 分钟 mp3 → faster-whisper 正常转写（看 n8n 日志）
- [ ] 手动 `/maintain` → `knowledge/` 增/更卡片，原文件归档到 `_processed/`
- [ ] 手动 `/ideate` → `inbox/ideas.md` 末尾追加新话题
- [ ] 手动 `/draft blog <topic>` → `output/blog/` 出现初稿
- [ ] 22:00 自动 `/maintain` 触发

---

## 排错速查

| 现象 | 原因 / 解法 |
|---|---|
| n8n 写文件提示权限 | Docker Desktop → Settings → Resources → File sharing 勾选 `D:\VScode\机器人` |
| `host.docker.internal` 不通 | 已在 compose 中加 `extra_hosts`；若仍不行用宿主机局域网 IP |
| Whisper 报 CUDA 错 | 设 `WHISPER_DEVICE=cpu`，或装 CUDA 12 + cuDNN 9 |
| Claude Code 提示 401/403 | `ANTHROPIC_AUTH_TOKEN` 未生效；关闭重开 PowerShell、`echo $env:ANTHROPIC_AUTH_TOKEN` 验证 |
| Claude Code 提示 `model not found` | 报错里的模型名不在智谱套餐内，调 `ANTHROPIC_MODEL`/`ANTHROPIC_SMALL_FAST_MODEL` 为套餐允许名（如 `glm-4.6` / `glm-4.5-air`） |
| Claude Code 命令找不到 4 个 slash | 检查工作目录是否 = Vault 根；`.claude/commands/*.md` 是否有 `description` frontmatter |
| Obsidian Git push 失败 | 在终端 `cd D:\VScode\机器人; git push` 看具体错误，多半是 SSH key 未配 |
| 转写中文识别成繁体 | WF1 OpenAI 节点 prompt 加 "请使用简体中文输出"；本地 server 已传 `language=zh` |

---

## 下一步可选增强

1. **Cloudflare Tunnel** 暴露 n8n 给手机直接 webhook（替代 Telegram polling）。
2. **第二个 AI 模型** 做认知对撞红队（n8n 调 GPT-4 → 结果回灌 Claude Code）。
3. **嵌入式 RAG**：当 `knowledge/` 卡片 > 500 张时，加 sqlite-vec 给 Claude Code 做语义检索。
4. **GitHub Action 自动发博**。
