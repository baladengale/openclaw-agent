"""Configuration management for OpenClaw Agent."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram
    telegram_bot_token: str = ""

    # Agent
    agent_name: str = "OpenClaw"
    agent_model: str = "default"
    log_level: str = "INFO"

    # Access control
    allowed_user_ids: list[int] = []

    model_config = {
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def parse_user_ids(cls, v: str | list) -> list[int]:
        if isinstance(v, list):
            return v
        if isinstance(v, str) and v.strip():
            return [int(uid.strip()) for uid in v.split(",") if uid.strip()]
        return []


def get_settings() -> Settings:
    """Create and return application settings."""
    return Settings()


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
    )
