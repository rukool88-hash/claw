#!/bin/bash
# Hermes cron job creators (idempotent)

PROMPT_MAINTAIN="执行 /maintain：扫描 inbox/transcripts 与 inbox/rss 中未处理的文件，按 /workspace/CLAUDE.md 第 4.1 节处理（最多 10 个），并把已处理文件移动到 _processed/。完成后把维护摘要发回 Telegram。"

# Remove any prior pkm-maintain job (avoid duplicates)
hermes cron list 2>/dev/null | awk '/Name:.*pkm-maintain/{found=1} found && /^  [a-f0-9]+ /{print $1; exit}' | while read -r jid; do
  [ -n "$jid" ] && hermes cron remove "$jid" 2>/dev/null || true
done

hermes cron create "0 22 * * *" \
  --name pkm-maintain \
  --workdir /workspace \
  --skill pkm-vault \
  --deliver telegram \
  "$PROMPT_MAINTAIN"

echo "---"
hermes cron list 2>&1 | tail -30
