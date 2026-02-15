"""Core OpenClaw Agent logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Conversation:
    """Tracks a conversation with a user."""

    user_id: int
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_message(self, role: str, content: str) -> Message:
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        return msg

    def get_context(self, max_messages: int = 20) -> list[dict]:
        """Return recent messages as context for the agent."""
        recent = self.messages[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in recent]

    def clear(self) -> None:
        self.messages.clear()


class OpenClawAgent:
    """The core OpenClaw agent that processes messages and generates responses.

    This agent maintains per-user conversations and provides a pluggable
    interface for extending with custom tools and commands.
    """

    BUILTIN_COMMANDS: dict[str, str] = {
        "/start": "Welcome to OpenClaw! I'm an experimental AI agent. Send me a message to get started.",
        "/help": (
            "Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/clear - Clear conversation history\n"
            "/status - Show agent status\n"
            "/about - About OpenClaw Agent"
        ),
        "/about": (
            "OpenClaw Agent v0.1.0\n"
            "An experimental AI agent with Telegram integration.\n"
            "https://github.com/baladengale/openclaw-agent"
        ),
    }

    def __init__(self, name: str = "OpenClaw") -> None:
        self.name = name
        self.conversations: dict[int, Conversation] = {}
        self._tools: dict[str, callable] = {}
        logger.info("OpenClaw Agent '%s' initialized", self.name)

    def get_conversation(self, user_id: int) -> Conversation:
        """Get or create a conversation for a user."""
        if user_id not in self.conversations:
            self.conversations[user_id] = Conversation(user_id=user_id)
        return self.conversations[user_id]

    def register_tool(self, name: str, handler: callable) -> None:
        """Register a custom tool/command handler."""
        self._tools[name] = handler
        logger.info("Tool registered: %s", name)

    async def process_message(self, user_id: int, text: str) -> str:
        """Process an incoming message and return a response.

        Handles built-in commands, registered tools, and general conversation.
        """
        text = text.strip()

        # Handle built-in commands
        if text in self.BUILTIN_COMMANDS:
            return self.BUILTIN_COMMANDS[text]

        # Handle /clear command
        if text == "/clear":
            conv = self.get_conversation(user_id)
            conv.clear()
            return "Conversation history cleared."

        # Handle /status command
        if text == "/status":
            return self._get_status(user_id)

        # Handle registered tools
        if text.startswith("/") and " " in text:
            cmd, args = text.split(" ", 1)
            if cmd in self._tools:
                return await self._tools[cmd](user_id, args)

        # General message processing
        conv = self.get_conversation(user_id)
        conv.add_message("user", text)

        response = await self._generate_response(conv)
        conv.add_message("assistant", response)

        return response

    async def _generate_response(self, conv: Conversation) -> str:
        """Generate a response based on conversation context.

        This is the core response generation method. Override or extend
        this to integrate with an LLM backend.
        """
        context = conv.get_context()
        last_message = context[-1]["content"] if context else ""

        # Default echo-style response for the base agent.
        # Replace this with an LLM API call for production use.
        return (
            f"[{self.name}] Received your message: \"{last_message}\"\n\n"
            "I'm running in default mode. Connect an LLM backend to enable "
            "intelligent responses. See /help for available commands."
        )

    def _get_status(self, user_id: int) -> str:
        conv = self.get_conversation(user_id)
        return (
            f"Agent: {self.name}\n"
            f"Status: Online\n"
            f"Your messages: {len(conv.messages)}\n"
            f"Active conversations: {len(self.conversations)}"
        )
