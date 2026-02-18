# OpenClaw Agent

An experimental AI agent with Telegram bot integration. OpenClaw provides a modular agent framework that can process messages, maintain per-user conversations, and run as a Telegram bot or interactive CLI.


## Network Architecture

All traffic is **outbound only** in the default configuration. No inbound ports are needed from the internet.

```
┌─────────────────────────────────────────────────────────┐
│                   Corporate Network                      │
│                                                          │
│  ┌──────────────────────┐                                │
│  │  Docker Container     │                                │
│  │  openclaw-gateway     │                                │
│  │  (port 18789)         │                                │
│  └──────┬───┬───┬────────┘                                │
│         │   │   │                                         │
│         │   │   │  ┌──────────────┐                       │
│         │   │   └──┤ Control UI   │  localhost:18789      │
│         │   │      │ (browser)    │  (inbound, local)     │
│         │   │      └──────────────┘                       │
│         │   │                                             │
└─────────┼───┼─────────────────────────────────────────────┘
          │   │
   ═══════╪═══╪══════ CORPORATE FIREWALL ═══════════════
          │   │
          │   │  OUTBOUND HTTPS (443) ONLY
          │   │
          │   ├──→ api.anthropic.com       (LLM inference)
          │   │
          │   └──→ api.telegram.org        (bot long-polling)
          │        ┌─────────────────┐
          │        │ Telegram polls   │
          │        │ getUpdates every │
          │        │ 30s (outbound)   │
          │        └─────────────────┘
          │
          └────→ registry.npmjs.org        (update check, optional)
```

### Communication Flow

| Connection | Direction | Domain | Port | Required? |
|---|---|---|---|---|
| Anthropic API | Outbound | `api.anthropic.com` | 443 | Yes (for Claude models) |
| Telegram Bot | Outbound | `api.telegram.org` | 443 | Yes (for Telegram channel) |
| Perplexity search | Outbound | `api.perplexity.ai` | 443 | No (if web search enabled) |
| NPM update check | Outbound | `registry.npmjs.org` | 443 | No (disable: `update.checkOnStart: false`) |
| Gateway UI | Inbound | localhost only | 18789 | Local access only |

- **Telegram** uses long-polling (`getUpdates`) by default -- outbound only, no webhook or inbound port needed.
- **No telemetry or analytics** -- zero usage data sent externally.
- **mDNS discovery** (UDP 5353) is on by default for LAN. Disable behind a firewall: `OPENCLAW_DISABLE_BONJOUR=1`.

### Minimum Firewall Rules

```bash
# Required -- outbound only
ALLOW TCP 443 -> api.anthropic.com
ALLOW TCP 443 -> api.telegram.org

# Optional
ALLOW TCP 443 -> api.perplexity.ai        # if web search enabled
ALLOW TCP 443 -> registry.npmjs.org        # if update checks wanted

# No inbound rules needed from the internet
```

## Installation

### Option 1: Local Install (Ubuntu/Debian)

```bash
bash install-openclaw.sh
```

Then run the onboarding wizard:

```bash
openclaw onboard --install-daemon
```

### Option 2: Docker

#### Prerequisites

- Docker Engine 20+ with Docker Compose v2
- User added to the `docker` group (`sudo usermod -aG docker $USER && newgrp docker`)

#### Clone and Build (Optimized)

The included multi-stage `Dockerfile` produces a slim ~900 MB image (vs ~4.2 GB single-stage).

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
docker build -t openclaw:optimized -f ../openclaw-agent/Dockerfile .
```

#### Option A: Fresh Setup with Docker Compose (No Host Config)

Uses a named Docker volume for all config/state -- no `~/.openclaw` directory needed on the host.

```bash
cd openclaw-agent

# 1. Create .env from the template
cp .env.example .env

# 2. Fill in your keys
#    ANTHROPIC_API_KEY=sk-ant-xxxxx
#    OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 32)
nano .env

# 3. Start the gateway
docker compose up -d openclaw-gateway

# 4. Run onboarding (interactive, one-time)
docker compose run --rm openclaw-cli onboard --no-install-daemon

# 5. Add Telegram channel
docker compose run --rm openclaw-cli channels add --channel telegram --token <BOT_TOKEN>

# 6. Approve Telegram pairing
docker compose run --rm openclaw-cli pairing approve telegram <pairing-code>
```

Access the Control UI at `http://127.0.0.1:18789/` and paste your gateway token.

#### Option B: Run with Existing Host Config

If you already have `~/.openclaw` configured from a local install:

```bash
# Generate a gateway token (or use existing one from ~/.openclaw/openclaw.json)
export OPENCLAW_GATEWAY_TOKEN=$(openssl rand -hex 32)

# Start the container (--user matches your host UID for file permissions)
docker run -d \
  --name openclaw-gateway \
  --restart unless-stopped \
  --user $(id -u):$(id -g) \
  -p 18789:18789 \
  -v ~/.openclaw:/home/node/.openclaw \
  -e HOME=/home/node \
  -e OPENCLAW_GATEWAY_TOKEN=$OPENCLAW_GATEWAY_TOKEN \
  openclaw:optimized \
  node openclaw.mjs gateway --allow-unconfigured --bind lan --port 18789
```

#### Manage the Container

```bash
# View logs
docker logs -f openclaw-gateway

# Stop
docker stop openclaw-gateway

# Start again
docker start openclaw-gateway

# Remove
docker stop openclaw-gateway && docker rm openclaw-gateway

# Docker Compose equivalents
docker compose logs -f openclaw-gateway
docker compose down
docker compose up -d openclaw-gateway
```

#### Port to Another Machine

```bash
# Export the optimized image (~900 MB)
docker save openclaw:optimized | gzip > openclaw-optimized.tar.gz

# On the target machine
docker load < openclaw-optimized.tar.gz
```

## Skills

### Market Overview (Python)

Real-time world market data with rich terminal tables — indices, commodities, crypto, forex, portfolio tracking, stock details, dividends, earnings, and financials.

```bash
# Default detail view (all world markets)
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py

# Summary view (key indices only)
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py -s

# Portfolio view (personal holdings)
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py -p

# Stock detail
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py -t NVDA

# Dividends / Earnings / Financials / Cashflow
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py -d AAPL
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py -e TSLA
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py -f NVDA
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py -c MSFT -q
```

| Dependency | Purpose |
|---|---|
| `uv` | Python script runner (PEP 723 inline deps) |
| `yfinance` | Yahoo Finance market data |
| `rich` | Terminal table rendering |
| `lxml`, `pandas` | HTML/data parsing |

**Cron:** Daily at 8:05 AM SGT via `daily_email.py` (sends HTML email with market summary + portfolio).

---

### Tech Intel Newsletter (Go)

Concurrent RSS aggregator that scores articles by keyword relevance and delivers a curated top-25 "Daily Market & Tech Pulse" HTML newsletter via Gmail SMTP.

```bash
# Run from compiled binary
~/.openclaw/workspace/skills/tech-intel/tech-intel

# Or build from source
cd skills/tech-intel && make run

# Run from Go source directly
go run skills/tech-intel/main.go

# To run the compiled binary on the server
export PATH=$HOME/go-sdk/go/bin:$HOME/go/bin:$PATH && /home/bala/.openclaw/workspace/skills/tech-intel/tech-intel 2>&1
```

| Feature | Detail |
|---|---|
| Language | Go 1.22+ (zero external dependencies, stdlib only) |
| RSS Feeds | 12 sources: TechCrunch, Ars Technica, The Verge, Hacker News, Wired, CNBC, MarketWatch, Yahoo Finance, Reuters, BBC, NPR |
| Concurrency | Fan-out goroutines per feed with buffered channels |
| Scoring | Keyword-based (AI, Semiconductor, Acquisition, FinTech, etc.) with title 2x bonus + recency bonus |
| Output | Top 25 articles, HTML email via Gmail SMTP + stdout summary |
| Fallback | Saves HTML to `~/.openclaw/workspace/` if email fails |

**Environment Variables** (loaded from `~/.openclaw/.env`):
- `GMAIL_USER` — Gmail address (default: your-email@example.com)
- `GMAIL_APP_PASSWORD` — Gmail app password (required for email)
- `NEWSLETTER_RECIPIENTS` — Comma-separated recipient list

**Cron:** Daily at 8:15 AM SGT (runs 10 min after market overview email).

---

## Cron Jobs

Both skills are scheduled via OpenClaw's built-in cron scheduler.

```bash
# List all scheduled jobs
openclaw cron list

# Manually trigger a job
openclaw cron run <job-id>

# Add a new job
openclaw cron add --name "Job Name" --cron "0 8 * * *" --tz "Asia/Singapore" \
  --session isolated --message "command to run" --wake next-heartbeat

# Enable / Disable
openclaw cron enable <job-id>
openclaw cron disable <job-id>
```

| Job | Schedule | Cron Expr |
|---|---|---|
| Daily Market Email | 8:05 AM SGT | `5 23 * * *` (UTC) |
| Daily Tech Intel Newsletter | 8:05 AM SGT | `5 23 * * *` (UTC) |

Cron config stored at: `~/.openclaw/cron/jobs.json`

---

## Syncing Skills to OpenClaw Workspace

Skills are developed in the project repo and synced to the OpenClaw workspace at `~/.openclaw/workspace/skills/`.

### Market Overview (Python)
```bash
# Copy updated script to workspace
cp market_overview.py ~/.openclaw/workspace/skills/market-overview/
cp skills/market-overview/SKILL.md ~/.openclaw/workspace/skills/market-overview/
```

### Tech Intel (Go)
```bash
# Build and sync (uses Makefile)
cd skills/tech-intel && make install

# Or manually:
cd skills/tech-intel
go build -ldflags="-s -w" -o tech-intel main.go
cp tech-intel SKILL.md template.html go.mod Makefile main.go \
   ~/.openclaw/workspace/skills/tech-intel/
```

---

## Exporting Skills to Another Computer

### Option 1: Git Clone (Recommended)

```bash
# On the target machine (macOS, Linux, etc.)
git clone git@github.com:baladengale/openclaw-agent.git
cd openclaw-agent
```

#### Market Overview (Python)
```bash
# Install uv (if not present)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run directly (uv auto-installs dependencies)
uv run --script skills/market-overview/market_overview.py -s
```

#### Tech Intel (Go)
```bash
# Install Go (if not present)
# macOS:
brew install go
# Linux:
curl -fsSL https://go.dev/dl/go1.22.5.linux-amd64.tar.gz | sudo tar -C /usr/local -xzf -

# Build for current platform
cd skills/tech-intel
make build
./tech-intel
```

### Option 2: Cross-Compile Go Binary

Build on the server, copy binary to target machine. No Go installation needed on target.

```bash
# On the build machine (this server)
cd skills/tech-intel

# For macOS (Apple Silicon)
make darwin
# Output: tech-intel-darwin-arm64

# For Linux (x86_64)
make linux
# Output: tech-intel-linux-amd64

# Copy to target
scp tech-intel-darwin-arm64 user@mac:/path/to/destination/
scp template.html user@mac:/path/to/destination/

# On the target machine — just run it
./tech-intel-darwin-arm64
```

### Option 3: Full Workspace Export

Export the entire OpenClaw workspace including all skills and configuration.

```bash
# On source machine
tar -czf openclaw-skills-export.tar.gz \
  -C ~/.openclaw/workspace skills/

# On target machine
mkdir -p ~/.openclaw/workspace
tar -xzf openclaw-skills-export.tar.gz -C ~/.openclaw/workspace/

# Re-add cron jobs on the new machine
openclaw cron add --name "Daily Tech Intel Newsletter" \
  --cron "15 23 * * *" --tz "Asia/Singapore" --session isolated \
  --message "Run this command and report the result: $(echo ~/.openclaw/workspace/skills/tech-intel/tech-intel)" \
  --wake next-heartbeat
```

### Option 4: Docker (Market Overview)

```bash
# Pull pre-built image
docker pull your-dockerhub-user/market-overview:latest

# Run portfolio view
docker run --rm your-dockerhub-user/market-overview -p

# Run stock detail
docker run --rm your-dockerhub-user/market-overview -t NVDA
```