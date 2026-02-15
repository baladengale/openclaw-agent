"""Telegram bot integration for OpenClaw Agent."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from openclaw_agent.agent import OpenClawAgent

logger = logging.getLogger(__name__)


class TelegramBot:
    """Wraps the OpenClaw agent as a Telegram bot.

    Handles incoming Telegram updates, routes them through the agent,
    and sends responses back to users.
    """

    def __init__(
        self,
        token: str,
        agent: OpenClawAgent,
        allowed_user_ids: list[int] | None = None,
    ) -> None:
        self.token = token
        self.agent = agent
        self.allowed_user_ids = set(allowed_user_ids) if allowed_user_ids else None
        self.application: Application | None = None

    def _is_authorized(self, user_id: int) -> bool:
        """Check if a user is authorized to use the bot."""
        if self.allowed_user_ids is None:
            return True
        return user_id in self.allowed_user_ids

    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle command messages (e.g., /start, /help)."""
        if not update.message or not update.effective_user:
            return

        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text("You are not authorized to use this bot.")
            return

        command = f"/{update.message.text.split()[0].lstrip('/')}" if update.message.text else ""
        logger.info("Command from user %d: %s", user_id, command)

        response = await self.agent.process_message(user_id, command)
        await update.message.reply_text(response)

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle regular text messages."""
        if not update.message or not update.effective_user or not update.message.text:
            return

        user_id = update.effective_user.id

        if not self._is_authorized(user_id):
            await update.message.reply_text("You are not authorized to use this bot.")
            return

        text = update.message.text
        logger.info("Message from user %d: %s", user_id, text[:50])

        response = await self.agent.process_message(user_id, text)
        await self._send_response(update, response)

    async def _send_response(self, update: Update, text: str) -> None:
        """Send a response, splitting long messages if necessary.

        Telegram has a 4096 character limit per message.
        """
        max_length = 4096
        if len(text) <= max_length:
            await update.message.reply_text(text)
            return

        # Split long messages at newline boundaries
        chunks: list[str] = []
        current = ""
        for line in text.split("\n"):
            if len(current) + len(line) + 1 > max_length:
                chunks.append(current)
                current = line
            else:
                current = f"{current}\n{line}" if current else line
        if current:
            chunks.append(current)

        for chunk in chunks:
            await update.message.reply_text(chunk)

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors from the Telegram bot."""
        logger.error("Telegram update caused error: %s", context.error, exc_info=context.error)

    def build(self) -> Application:
        """Build the Telegram Application with all handlers."""
        self.application = Application.builder().token(self.token).build()

        # Register command handlers
        commands = ["start", "help", "clear", "status", "about"]
        for cmd in commands:
            self.application.add_handler(CommandHandler(cmd, self._handle_command))

        # Register message handler for all non-command text
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )

        # Register error handler
        self.application.add_error_handler(self._error_handler)

        logger.info("Telegram bot built with %d command handlers", len(commands))
        return self.application

    def run(self) -> None:
        """Start the bot in polling mode (blocking)."""
        if not self.application:
            self.build()

        logger.info("Starting OpenClaw Telegram bot in polling mode...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
