# OpenClaw Agent

An experimental AI agent with Telegram bot integration. OpenClaw provides a modular agent framework that can process messages, maintain per-user conversations, and run as a Telegram bot or interactive CLI.

## Features

- **Telegram Bot** - Full integration via `python-telegram-bot`, with polling-based message handling
- **Per-user Conversations** - Each user gets isolated conversation history with context tracking
- **Built-in Commands** - `/start`, `/help`, `/clear`, `/status`, `/about`
- **Access Control** - Optionally restrict the bot to specific Telegram user IDs
- **CLI Mode** - Interactive command-line mode for local testing without Telegram
- **Extensible Tools** - Register custom command handlers on the agent
- **Long Message Splitting** - Automatically splits responses that exceed Telegram's 4096 char limit

## Project Structure

```
openclaw-agent/
├── src/openclaw_agent/
│   ├── __init__.py          # Package init
│   ├── agent.py             # Core agent logic and conversation management
│   ├── config.py            # Configuration via environment variables
│   ├── main.py              # CLI entry point (telegram / cli modes)
│   └── telegram_bot.py      # Telegram bot integration layer
├── tests/
│   ├── test_agent.py        # Agent unit tests
│   └── test_config.py       # Config unit tests
├── .env.example             # Example environment config
├── pyproject.toml           # Project metadata and dependencies
└── README.md
```

## Prerequisites

- Python 3.10+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

## Installation

```bash
# Clone the repository
git clone https://github.com/baladengale/openclaw-agent.git
cd openclaw-agent

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install the package
pip install -e .

# For development (includes test/lint tools)
pip install -e ".[dev]"
```

## Configuration

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required: Your Telegram bot token from @BotFather
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here

# Optional: Restrict access to specific Telegram user IDs
ALLOWED_USER_IDS=123456789,987654321

# Optional: Customize agent name and log level
AGENT_NAME=OpenClaw
LOG_LEVEL=INFO
```

### Getting a Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts to name your bot
3. Copy the token and paste it into your `.env` file

## Usage

### Telegram Bot Mode (default)

```bash
openclaw
# or
openclaw --mode telegram
```

The bot will start polling for messages. Send `/start` to your bot on Telegram to begin.

### CLI Mode

```bash
openclaw --mode cli
```

This starts an interactive shell where you can test the agent locally without needing Telegram.

### Running Directly

```bash
python -m openclaw_agent.main
```

## Bot Commands

| Command   | Description                    |
|-----------|--------------------------------|
| `/start`  | Welcome message                |
| `/help`   | Show available commands        |
| `/clear`  | Clear your conversation history|
| `/status` | Show agent status              |
| `/about`  | About OpenClaw Agent           |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
```

## Extending the Agent

Register custom tools on the agent:

```python
from openclaw_agent.agent import OpenClawAgent

agent = OpenClawAgent(name="MyAgent")

async def weather_tool(user_id: int, args: str) -> str:
    return f"Weather for {args}: Sunny, 22C"

agent.register_tool("/weather", weather_tool)
```

## License

MIT
