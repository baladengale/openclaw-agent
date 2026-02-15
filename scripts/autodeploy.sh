#!/usr/bin/env bash
# OpenClaw Agent - Auto-Deploy Script
# Runs on EC2 when triggered by GitHub Actions (or manually).
# Pulls latest code, reinstalls, and restarts the service.

set -euo pipefail

APP_DIR="${OPENCLAW_DIR:-/home/ubuntu/openclaw-agent}"
SERVICE_NAME="openclaw"
BRANCH="${1:-main}"

cd "$APP_DIR"

echo "--- Pulling latest from origin/$BRANCH ---"
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

echo "--- Installing dependencies ---"
source "$APP_DIR/.venv/bin/activate"
pip install -e "$APP_DIR" -q

echo "--- Restarting service ---"
sudo systemctl restart "$SERVICE_NAME"
sleep 2

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "--- Deploy successful. Bot is running. ---"
else
    echo "--- Deploy WARNING: service may not be healthy ---"
    sudo journalctl -u "$SERVICE_NAME" -n 10 --no-pager
    exit 1
fi
