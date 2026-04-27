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

### API Key 准备
- [ ] Anthropic API Key（<https://console.anthropic.com>）
- [ ] OpenAI API Key（<https://platform.openai.com>）
- [ ] Telegram Bot Token（在 @BotFather 创建）
- [ ] Readwise / Inoreader 账号（可选，先跳过）
- [ ] GitHub 账号 + 已 `gh auth login`

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

## 2. 第四层：Claude Code AI 引擎

```powershell
# 全局安装
npm install -g @anthropic-ai/claude-code

# 在 Vault 根目录初始化
cd D:\VScode\机器人
claude   # 第一次会引导登录 Anthropic 账号
```

进入 Claude Code 后：
1. 它会自动加载 [CLAUDE.md](CLAUDE.md) 和 [.claude/settings.json](.claude/settings.json)。
2. 验证 4 个 Slash 命令：在 prompt 里输入 `/` 应能补全 `/maintain` `/ideate` `/debate` `/draft`。

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
- **OpenAI**：粘贴 OpenAI Key
- **Anthropic**：粘贴 Anthropic Key
- **Telegram**：粘贴 Bot Token
- （后续按需）Readwise / Inoreader / IMAP

### ✅ 验证
- n8n 中创建一个 Manual Trigger → Write Binary File 节点 → 路径 `/vault/inbox/transcripts/test-from-n8n.md` → 内容随意 → Execute。
- 宿主机的 `inbox/transcripts/test-from-n8n.md` 应出现。

---

## 4. 4 个核心工作流（在 n8n UI 创建并保存）

> 每个工作流创建完后导出 JSON 到 [infra/n8n/workflows/](infra/n8n/workflows/) 提交入库。

### WF1 — 手机录音 → 转写
节点链：
1. **Telegram Trigger**（事件：`message`，含 voice/audio）
2. **Telegram → Get File**（下载到 binary）
3. **Write Binary File**：`/vault/inbox/audio/{{ $now.format('yyyyMMdd-HHmmss') }}-{{$json.message.message_id}}.ogg`
4. **IF**：判断 `message.voice.duration > 300`（>5 分钟走本地）
   - true → **HTTP Request** `POST http://host.docker.internal:9000/transcribe` body `{"path":"/vault/inbox/audio/<上一步文件名>","language":"zh"}`
   - false → **OpenAI** node → Audio → Transcribe（model `whisper-1`）
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
2. **Execute Command**（n8n 自带，需开启 `N8N_RUNNERS_ENABLED`）：
   ```
   cmd: powershell -NoProfile -Command "cd D:\VScode\机器人; claude --print --command '/maintain'"
   ```
   > 也可以用 SSH 节点连本机；或写一个 batch 脚本。
3. **IF** 失败 → Telegram 通知用户。

> Claude Code CLI 的 `--print --command` 形式具体参数以你安装版本为准（用 `claude --help` 查），如果不支持，把命令改成 `claude` 进入交互再 echo 注入，或写个包装脚本。

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
| Claude Code 命令找不到 4 个 slash | 检查工作目录是否 = Vault 根；`.claude/commands/*.md` 是否有 `description` frontmatter |
| Obsidian Git push 失败 | 在终端 `cd D:\VScode\机器人; git push` 看具体错误，多半是 SSH key 未配 |
| 转写中文识别成繁体 | WF1 OpenAI 节点 prompt 加 "请使用简体中文输出"；本地 server 已传 `language=zh` |

---

## 下一步可选增强

1. **Cloudflare Tunnel** 暴露 n8n 给手机直接 webhook（替代 Telegram polling）。
2. **第二个 AI 模型** 做认知对撞红队（n8n 调 GPT-4 → 结果回灌 Claude Code）。
3. **嵌入式 RAG**：当 `knowledge/` 卡片 > 500 张时，加 sqlite-vec 给 Claude Code 做语义检索。
4. **GitHub Action 自动发博**。
