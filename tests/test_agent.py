"""Tests for the OpenClaw Agent core module."""

import pytest

from openclaw_agent.agent import Conversation, Message, OpenClawAgent


class TestMessage:
    def test_message_creation(self):
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"
        assert msg.timestamp is not None


class TestConversation:
    def test_add_message(self):
        conv = Conversation(user_id=123)
        msg = conv.add_message("user", "hello")
        assert len(conv.messages) == 1
        assert msg.content == "hello"

    def test_get_context(self):
        conv = Conversation(user_id=123)
        conv.add_message("user", "hello")
        conv.add_message("assistant", "hi there")
        context = conv.get_context()
        assert len(context) == 2
        assert context[0] == {"role": "user", "content": "hello"}
        assert context[1] == {"role": "assistant", "content": "hi there"}

    def test_get_context_max_messages(self):
        conv = Conversation(user_id=123)
        for i in range(30):
            conv.add_message("user", f"message {i}")
        context = conv.get_context(max_messages=5)
        assert len(context) == 5
        assert context[0]["content"] == "message 25"

    def test_clear(self):
        conv = Conversation(user_id=123)
        conv.add_message("user", "hello")
        conv.clear()
        assert len(conv.messages) == 0


class TestOpenClawAgent:
    @pytest.fixture
    def agent(self):
        return OpenClawAgent(name="TestAgent")

    @pytest.mark.asyncio
    async def test_start_command(self, agent):
        response = await agent.process_message(1, "/start")
        assert "Welcome" in response

    @pytest.mark.asyncio
    async def test_help_command(self, agent):
        response = await agent.process_message(1, "/help")
        assert "/start" in response
        assert "/help" in response
        assert "/clear" in response

    @pytest.mark.asyncio
    async def test_clear_command(self, agent):
        await agent.process_message(1, "hello")
        response = await agent.process_message(1, "/clear")
        assert "cleared" in response.lower()
        assert len(agent.get_conversation(1).messages) == 0

    @pytest.mark.asyncio
    async def test_status_command(self, agent):
        response = await agent.process_message(1, "/status")
        assert "TestAgent" in response
        assert "Online" in response

    @pytest.mark.asyncio
    async def test_about_command(self, agent):
        response = await agent.process_message(1, "/about")
        assert "OpenClaw" in response

    @pytest.mark.asyncio
    async def test_general_message(self, agent):
        response = await agent.process_message(1, "hello world")
        assert "hello world" in response

    @pytest.mark.asyncio
    async def test_conversation_tracking(self, agent):
        await agent.process_message(1, "first message")
        await agent.process_message(1, "second message")
        conv = agent.get_conversation(1)
        # Each message adds user + assistant
        assert len(conv.messages) == 4

    @pytest.mark.asyncio
    async def test_separate_conversations(self, agent):
        await agent.process_message(1, "user 1 message")
        await agent.process_message(2, "user 2 message")
        assert len(agent.conversations) == 2

    def test_register_tool(self, agent):
        async def my_tool(user_id, args):
            return f"tool result: {args}"

        agent.register_tool("/mytool", my_tool)
        assert "/mytool" in agent._tools
