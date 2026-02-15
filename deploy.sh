#!/usr/bin/env bash
# OpenClaw Agent - EC2 Deployment Script
# Usage: bash deploy.sh
#
# This script:
#   1. Installs system dependencies (Python 3, venv, git)
#   2. Sets up the Python virtual environment
#   3. Installs the openclaw-agent package
#   4. Prompts for your Telegram bot token
#   5. Creates a systemd service for auto-start on boot
#   6. Starts the bot

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="openclaw"
VENV_DIR="$APP_DIR/.venv"
ENV_FILE="$APP_DIR/.env"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
CURRENT_USER="$(whoami)"

echo "============================================"
echo "  OpenClaw Agent - EC2 Deployment"
echo "============================================"
echo ""
echo "Project directory: $APP_DIR"
echo "Running as user:   $CURRENT_USER"
echo ""

# --- 1. System dependencies ---
echo "[1/6] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv > /dev/null
echo "       Done."

# --- 2. Python virtual environment ---
echo "[2/6] Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
echo "       Done. Python: $(python3 --version)"

# --- 3. Install the package ---
echo "[3/6] Installing openclaw-agent..."
pip install --upgrade pip -q
pip install -e "$APP_DIR" -q
echo "       Done."

# --- 4. Configure .env ---
echo "[4/6] Configuring environment..."
if [ -f "$ENV_FILE" ]; then
    echo "       .env file already exists."
    # Check if token is set
    if grep -q "^TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here" "$ENV_FILE" 2>/dev/null || \
       grep -q "^TELEGRAM_BOT_TOKEN=$" "$ENV_FILE" 2>/dev/null; then
        echo ""
        read -rp "       Enter your Telegram Bot Token (from @BotFather): " BOT_TOKEN
        sed -i "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=${BOT_TOKEN}|" "$ENV_FILE"
        echo "       Token saved."
    else
        echo "       Telegram token already configured."
    fi
else
    cp "$APP_DIR/.env.example" "$ENV_FILE"
    echo ""
    read -rp "       Enter your Telegram Bot Token (from @BotFather): " BOT_TOKEN
    sed -i "s|^TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=${BOT_TOKEN}|" "$ENV_FILE"
    echo "       Token saved."
fi

# Optional: allowed user IDs
echo ""
read -rp "       Restrict to specific Telegram user IDs? (comma-separated, or Enter to skip): " USER_IDS
if [ -n "$USER_IDS" ]; then
    sed -i "s|^ALLOWED_USER_IDS=.*|ALLOWED_USER_IDS=${USER_IDS}|" "$ENV_FILE"
    echo "       Access restricted to: $USER_IDS"
fi

# --- 5. Create systemd service ---
echo ""
echo "[5/6] Setting up systemd service..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=OpenClaw Telegram Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/openclaw
Restart=on-failure
RestartSec=5
EnvironmentFile=$ENV_FILE

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
echo "       Service created and enabled."

# --- 6. Start the bot ---
echo "[6/6] Starting OpenClaw bot..."
sudo systemctl restart "$SERVICE_NAME"
sleep 2

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo ""
    echo "============================================"
    echo "  OpenClaw is RUNNING!"
    echo "============================================"
    echo ""
    echo "  Send /start to your bot on Telegram."
    echo ""
    echo "  Useful commands:"
    echo "    Status:   sudo systemctl status openclaw"
    echo "    Logs:     sudo journalctl -u openclaw -f"
    echo "    Stop:     sudo systemctl stop openclaw"
    echo "    Restart:  sudo systemctl restart openclaw"
    echo ""
else
    echo ""
    echo "  WARNING: Service may not have started correctly."
    echo "  Check logs: sudo journalctl -u openclaw -n 20"
    echo ""
fi
