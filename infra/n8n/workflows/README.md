# n8n Workflows

可一键导入。在 n8n 主界面 → 左下角 ··· 菜单 → **Import from File** → 选对应 JSON。

## 文件
| 文件 | 用途 | 导入后需要做的修改 |
|---|---|---|
| `wf1-voice-transcribe.json` | Telegram 语音 → 本地 Whisper → 写入 `inbox/transcripts/` | 选 Telegram 凭证；激活开关 |
| `wf2-rss-ingest.json` | Webhook 接收 RSS / 书摘 → 追加到 `inbox/rss/<日期>.md` | 复制 Webhook URL 给 IFTTT/Inoreader |
| `wf4-maintain-notify.json` | 每天 22:00 给自己 Telegram 发提醒（实际 /maintain 走 schtasks） | 选 Telegram 凭证；填你的 chat_id；激活 |

## 导入步骤
1. n8n 主界面 → **Workflows** → 顶部 **+ Add Workflow** 旁的下拉 → **Import from File**
2. 选 JSON → 自动打开
3. 红色节点表示缺凭证：点击节点 → Credential 选你建好的（如 `Telegram`）
4. 顶部点 **Save** → 切右上 **Active** 开关

## 拿到 Telegram chat_id 的快捷方法
1. WF1 激活后给 Bot 发任意一句话
2. n8n WF1 → Executions → 点最近一条 → Telegram Trigger 输出 → `message.chat.id` 就是
3. 复制粘到 WF4 替换 `REPLACE_ME_YOUR_CHAT_ID`
