#!/bin/bash
# Container entrypoint: start Hermes gateway in background, then run sshd in foreground.
# This is the CMD for ubuntu24-dev:hermes-v1.

set -e

mkdir -p /root/.hermes/logs

# Start Hermes gateway in background as root.
# Use a login shell so /root/.bashrc / .profile get sourced (PATH, locale, etc.).
nohup /bin/bash -lc 'hermes gateway run' \
  > /root/.hermes/logs/gateway.log 2>&1 < /dev/null &
disown

echo "[start-hermes-stack] hermes gateway launched (logs: /root/.hermes/logs/gateway.log)"

# sshd in foreground keeps PID 1
exec /usr/sbin/sshd -D -e
