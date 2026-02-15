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

# --- 5. Make autodeploy script executable ---
echo "[5/7] Setting up autodeploy script..."
chmod +x "$APP_DIR/scripts/autodeploy.sh"
# Allow the deploy user to restart the service without a password prompt
SUDOERS_LINE="$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart openclaw, /usr/bin/systemctl stop openclaw, /usr/bin/systemctl start openclaw"
if ! sudo grep -qF "$SUDOERS_LINE" /etc/sudoers.d/openclaw 2>/dev/null; then
    echo "$SUDOERS_LINE" | sudo tee /etc/sudoers.d/openclaw > /dev/null
    sudo chmod 440 /etc/sudoers.d/openclaw
fi
echo "       Done."

# --- 6. Create systemd service ---
echo ""
echo "[6/7] Setting up systemd service..."
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

# --- 7. Start the bot ---
echo "[7/7] Starting OpenClaw bot..."
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
    echo "  --- Auto-Deploy (GitHub Actions) ---"
    echo "  To enable push-to-deploy, add these GitHub secrets:"
    echo "    EC2_HOST     = your EC2 public IP or hostname"
    echo "    EC2_USER     = ubuntu"
    echo "    EC2_SSH_KEY  = contents of your .pem private key"
    echo ""
    echo "  Then every push to main auto-deploys here."
    echo ""
else
    echo ""
    echo "  WARNING: Service may not have started correctly."
    echo "  Check logs: sudo journalctl -u openclaw -n 20"
    echo ""
fi
