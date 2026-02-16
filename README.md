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

## skills market overview 
```
uv run --script ~/.openclaw/workspace/skills/market-overview/market_overview.py
```