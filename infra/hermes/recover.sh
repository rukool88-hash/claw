#!/bin/bash
# Recover-Hermes — re-apply Vault PKM config to a fresh Hermes install in ubuntu24.
#
# RUN THIS FROM THE HOST (Linux/macOS/WSL/Git-Bash). It uses `docker exec` to
# reach into the container — DO NOT run it from inside the container.
# On Windows PowerShell, use `recover.ps1` instead.
#
# Prerequisites:
#   1. ubuntu24 container is running (image: ubuntu24-dev:latest or hermes-v2)
#   2. Hermes Agent is installed inside (binary at /usr/local/bin/hermes)
#   3. GLM_API_KEY + TELEGRAM_BOT_TOKEN already written to /root/.hermes/.env
#      (see README "首次或灾难恢复" 流程)
#
# Idempotent — safe to run multiple times.

set -e

CONTAINER=${HERMES_CONTAINER:-ubuntu24}

if ! docker exec "$CONTAINER" bash -lc 'command -v hermes' >/dev/null 2>&1; then
  echo "✗ hermes binary not found in container '$CONTAINER'."
  echo "  Install Hermes first, then re-run this script."
  exit 1
fi

echo "◆ Recovering Hermes config in container '$CONTAINER'..."

# 1. GLM-4.6 .env (idempotent)
echo "  [1/6] Configuring GLM-4.6 in .env..."
docker exec "$CONTAINER" bash -lc '
  : "${GLM_API_KEY_VALUE:=dd9e9fc3142b4b438401415d584d86c6.753HZ3QgCaBNghx0}"
  if grep -q "^GLM_API_KEY=" ~/.hermes/.env 2>/dev/null; then
    sed -i "s|^GLM_API_KEY=.*|GLM_API_KEY=$GLM_API_KEY_VALUE|" ~/.hermes/.env
  else
    sed -i "s|^# GLM_API_KEY=.*|GLM_API_KEY=$GLM_API_KEY_VALUE|" ~/.hermes/.env
  fi
  if grep -q "^GLM_BASE_URL=" ~/.hermes/.env; then
    sed -i "s|^GLM_BASE_URL=.*|GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4|" ~/.hermes/.env
  else
    sed -i "s|^# GLM_BASE_URL=.*|GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4|" ~/.hermes/.env
  fi
'

# 2. Set default model
echo "  [2/6] Setting default model = glm-4.6..."
docker exec "$CONTAINER" bash -lc '
  hermes config set model.default glm-4.6 >/dev/null
  hermes config set model.provider glm >/dev/null
  hermes config set model.base_url https://open.bigmodel.cn/api/paas/v4 >/dev/null
'

# 3. Install pkm-vault skill
echo "  [3/6] Installing pkm-vault skill..."
docker exec "$CONTAINER" bash -lc '
  mkdir -p ~/.hermes/skills/pkm-vault
  cp /workspace/infra/hermes/skills/pkm-vault/SKILL.md ~/.hermes/skills/pkm-vault/SKILL.md
'

# 4. Install SOUL.md persona
echo "  [4/6] Installing SOUL.md..."
docker exec "$CONTAINER" bash -lc '
  cp /workspace/infra/hermes/SOUL.md ~/.hermes/SOUL.md
'

# 5. Re-create cron pkm-maintain
echo "  [5/6] Creating cron pkm-maintain..."
docker exec "$CONTAINER" /usr/local/lib/hermes-agent/venv/bin/python3 \
  /workspace/infra/hermes/create_cron.py >/dev/null

# 6. Enable webhook + create rss-ingest
echo "  [6/6] Enabling webhook + creating rss-ingest..."
docker exec "$CONTAINER" /usr/local/lib/hermes-agent/venv/bin/python3 \
  /workspace/infra/hermes/setup_webhook.py >/dev/null

# Restart gateway so config changes take effect
echo "◆ Restarting gateway..."
docker exec "$CONTAINER" bash -lc '
  pkill -f "hermes gateway run" 2>/dev/null || true
  sleep 2
  nohup bash -lc "hermes gateway run" > ~/.hermes/logs/gateway.log 2>&1 < /dev/null &
  disown
'

sleep 4
echo
echo "◆ Final status:"
docker exec "$CONTAINER" bash -lc 'hermes status 2>&1 | grep -E "Model:|Provider:|Telegram|QQBot|Webhook|Status:|Jobs:"'
echo
docker exec "$CONTAINER" bash -lc 'hermes cron list 2>&1 | grep -E "Name:|Schedule:|Next run:" | head -10'
echo
echo "✓ Recovery complete."
echo "  Webhook URL (RSS): http://localhost:8644/webhooks/rss-ingest"
echo "  Get secret: docker exec $CONTAINER cat /root/.hermes/webhook_subscriptions.json | grep secret"
