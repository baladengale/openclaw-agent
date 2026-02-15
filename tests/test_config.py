"""Tests for configuration module."""

from openclaw_agent.config import Settings


class TestSettings:
    def test_default_settings(self):
        settings = Settings(telegram_bot_token="test-token")
        assert settings.agent_name == "OpenClaw"
        assert settings.log_level == "INFO"
        assert settings.allowed_user_ids == []

    def test_parse_user_ids_from_string(self):
        settings = Settings(
            telegram_bot_token="test",
            allowed_user_ids="123,456,789",
        )
        assert settings.allowed_user_ids == [123, 456, 789]

    def test_parse_user_ids_empty_string(self):
        settings = Settings(
            telegram_bot_token="test",
            allowed_user_ids="",
        )
        assert settings.allowed_user_ids == []

    def test_parse_user_ids_from_list(self):
        settings = Settings(
            telegram_bot_token="test",
            allowed_user_ids=[1, 2, 3],
        )
        assert settings.allowed_user_ids == [1, 2, 3]
