#!/bin/bash
set -e
set -o pipefail

# This script should be run as a normal user (not root/sudo).
# It will use sudo internally only for apt commands.
if [ "$(id -u)" -eq 0 ]; then
    echo "ERROR: Do not run this script as root or with sudo."
    echo "Run it as your normal user instead:"
    echo "  bash install-openclaw.sh"
    exit 1
fi

echo "========================================="
echo "  OpenClaw Installation Script"
echo "  With Telegram Integration"
echo "========================================="
echo ""

# ---- 1. Update system ----
echo "[1/6] Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# ---- 2. Install prerequisites ----
echo "[2/6] Installing prerequisites..."
sudo apt install -y curl build-essential libssl-dev git

# ---- 3. Install NVM (idempotent) ----
echo "[3/6] Installing NVM..."
export NVM_DIR="$HOME/.nvm"
if [ ! -d "$NVM_DIR" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
else
    echo "NVM already installed, skipping."
fi

# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# ---- 4. Install Node.js 22 ----
echo "[4/6] Installing Node.js v22..."
if ! nvm ls 22 >/dev/null 2>&1; then
    nvm install 22
else
    echo "Node.js v22 already installed, skipping."
fi
nvm alias default 22
nvm use default

echo "Node: $(node -v) | NPM: $(npm -v)"

# ---- 5. Install Homebrew (Linuxbrew) ----
echo "[5/6] Installing Homebrew..."
if ! command -v brew &>/dev/null; then
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Add brew to PATH for this session
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv 2>/dev/null || true)"
else
    echo "Homebrew already installed, skipping."
fi

# ---- 6. Install OpenClaw ----
echo "[6/6] Installing OpenClaw..."
curl -fsSL https://openclaw.ai/install.sh | bash

echo ""
echo "========================================="
echo "  Installation complete!"
echo "========================================="
echo ""
echo "Next steps (interactive setup):"
echo ""
echo "  1. Run the onboarding wizard:"
echo "     openclaw onboard --install-daemon"
echo ""
echo "  2. During setup, select:"
echo "     - QuickStart"
echo "     - Anthropic as provider"
echo "     - Enter your Anthropic API key"
echo "     - Select model: anthropic/claude-sonnet-4-5"
echo "     - Select channel: Telegram (Bot API)"
echo "     - Enter your Telegram Bot Token"
echo ""
echo "  3. After setup, approve Telegram pairing:"
echo "     openclaw pairing approve telegram <pairing-code>"
echo ""
echo "  4. Useful commands:"
echo "     openclaw doctor        # Check configuration"
echo "     openclaw gateway       # Start the gateway"
echo "     systemctl status openclaw  # Check service status"
echo ""
echo "========================================="
