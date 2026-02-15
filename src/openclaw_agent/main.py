"""Entry point for the OpenClaw Agent."""

from __future__ import annotations

import argparse
import sys

from openclaw_agent.agent import OpenClawAgent
from openclaw_agent.config import get_settings, setup_logging
from openclaw_agent.telegram_bot import TelegramBot


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the OpenClaw Agent CLI."""
    parser = argparse.ArgumentParser(
        prog="openclaw",
        description="OpenClaw Agent - An experimental AI agent with Telegram integration",
    )
    parser.add_argument(
        "--mode",
        choices=["telegram", "cli"],
        default="telegram",
        help="Run mode: 'telegram' for bot polling, 'cli' for interactive shell (default: telegram)",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    setup_logging(settings.log_level)

    agent = OpenClawAgent(name=settings.agent_name)

    if args.mode == "telegram":
        return _run_telegram(agent, settings)
    else:
        return _run_cli(agent)


def _run_telegram(agent: OpenClawAgent, settings) -> int:
    """Start the Telegram bot."""
    if not settings.telegram_bot_token:
        print(
            "Error: TELEGRAM_BOT_TOKEN is not set.\n"
            "1. Talk to @BotFather on Telegram to create a bot\n"
            "2. Copy the token into your .env file\n"
            "   See .env.example for reference."
        )
        return 1

    bot = TelegramBot(
        token=settings.telegram_bot_token,
        agent=agent,
        allowed_user_ids=settings.allowed_user_ids or None,
    )
    bot.run()
    return 0


def _run_cli(agent: OpenClawAgent) -> int:
    """Run the agent in interactive CLI mode."""
    import asyncio

    print(f"OpenClaw Agent - Interactive CLI Mode")
    print(f"Agent: {agent.name}")
    print("Type /help for commands, /quit to exit.\n")

    async def _loop():
        user_id = 0  # CLI user
        while True:
            try:
                user_input = input("You> ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if user_input.strip() in ("/quit", "/exit"):
                print("Goodbye!")
                break

            response = await agent.process_message(user_id, user_input)
            print(f"\n{agent.name}> {response}\n")

    asyncio.run(_loop())
    return 0


if __name__ == "__main__":
    sys.exit(main())
