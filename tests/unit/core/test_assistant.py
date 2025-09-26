"""Tests for Jarvis Assistant."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from jarvis_shared.models import Message, MessageRole, LLMResponse, ToolCall, ToolResult
from jarvis_core.assistant import JarvisAssistant


class TestJarvisAssistant:
    """Test JarvisAssistant class."""

    @pytest.fixture
    def assistant(self, mock_config):
        """Create assistant instance with mocked dependencies."""
        with (
            patch("jarvis_core.assistant.LLMService"),
            patch("jarvis_core.assistant.MCPClient"),
            patch("jarvis_core.assistant.get_logger") as mock_get_logger,
        ):

            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            assistant = JarvisAssistant(mock_config)
            assistant.llm_service = AsyncMock()
            assistant.mcp_client = AsyncMock()
            assistant.logger = mock_logger

            return assistant

    @pytest.mark.asyncio
    async def test_initialize(self, assistant):
        """Test assistant initialization."""
        assistant.mcp_client.connect = AsyncMock()

        await assistant.initialize()

        assistant.mcp_client.connect.assert_called_once()
        assert len(assistant.conversation_history) == 1
        assert assistant.conversation_history[0].role == MessageRole.SYSTEM

    @pytest.mark.asyncio
    async def test_process_command_simple(self, assistant):
        """Test processing a simple command without tools."""
        # Setup
        await assistant.initialize()

        assistant.mcp_client.list_tools = AsyncMock(return_value=[])
        assistant.llm_service.chat = AsyncMock(
            return_value=LLMResponse(
                content="Hello! I'm Jarvis, how can I help you?", model="mistral:7b"
            )
        )

        # Execute
        response = await assistant.process_command("Hello")

        # Verify
        assert response == "Hello! I'm Jarvis, how can I help you?"
        assert len(assistant.conversation_history) == 3  # System + User + Assistant
        assistant.llm_service.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_command_with_tools(self, assistant):
        """Test processing a command that uses tools."""
        # Setup
        await assistant.initialize()

        tools = [
            {
                "name": "gmail_read_emails",
                "description": "Read emails",
                "parameters": {"type": "object"},
            }
        ]

        tool_call = ToolCall(
            id="call_123", name="gmail_read_emails", arguments={"query": "unread"}
        )

        llm_response = LLMResponse(
            content="I'll check your emails.",
            tool_calls=[tool_call],
            model="mistral:7b",
        )

        tool_result = ToolResult(
            tool_call_id="call_123",
            content='{"emails": [{"subject": "Test"}]}',
            success=True,
        )

        final_response = LLMResponse(
            content="You have 1 unread email with subject 'Test'.", model="mistral:7b"
        )

        assistant.mcp_client.list_tools = AsyncMock(return_value=tools)
        assistant.llm_service.chat = AsyncMock(
            side_effect=[llm_response, final_response]
        )
        assistant.mcp_client.execute_tool = AsyncMock(return_value=tool_result)

        # Execute
        response = await assistant.process_command("Check my emails")

        # Verify
        assert response == "You have 1 unread email with subject 'Test'."
        assert assistant.llm_service.chat.call_count == 2
        assistant.mcp_client.execute_tool.assert_called_once_with(tool_call)

    @pytest.mark.asyncio
    async def test_process_command_stream_simple(self, assistant):
        """Test streaming a simple command."""
        # Setup
        await assistant.initialize()

        assistant.mcp_client.list_tools = AsyncMock(return_value=[])

        async def mock_stream():
            tokens = ["Hello", " there", "! How", " can I", " help?"]
            for token in tokens:
                yield token

        assistant.llm_service.chat_stream = AsyncMock(return_value=mock_stream())

        # Execute
        full_response = ""
        async for token in assistant.process_command_stream("Hello"):
            full_response += token

        # Verify
        assert full_response == "Hello there! How can I help?"
        assert len(assistant.conversation_history) == 3  # System + User + Assistant

    @pytest.mark.asyncio
    async def test_process_command_stream_with_tools(self, assistant):
        """Test streaming command that requires tools."""
        # Setup
        await assistant.initialize()

        tools = [
            {
                "name": "gmail_read_emails",
                "description": "Read emails",
                "parameters": {"type": "object"},
            }
        ]

        tool_call = ToolCall(
            id="call_123", name="gmail_read_emails", arguments={"query": "unread"}
        )

        # First response with tool calls
        llm_response = LLMResponse(
            content="I'll check your emails.",
            tool_calls=[tool_call],
            model="mistral:7b",
        )

        tool_result = ToolResult(
            tool_call_id="call_123", content='{"emails": []}', success=True
        )

        # Streaming final response
        async def mock_stream():
            tokens = ["You have", " no", " unread", " emails."]
            for token in tokens:
                yield token

        assistant.mcp_client.list_tools = AsyncMock(return_value=tools)
        assistant.llm_service.chat = AsyncMock(return_value=llm_response)
        assistant.mcp_client.execute_tool = AsyncMock(return_value=tool_result)
        assistant.llm_service.chat_stream = AsyncMock(return_value=mock_stream())

        # Execute (command contains "email" keyword to trigger tools)
        full_response = ""
        async for token in assistant.process_command_stream("Check my email"):
            full_response += token

        # Verify
        assert full_response == "You have no unread emails."
        assistant.mcp_client.execute_tool.assert_called_once_with(tool_call)

    def test_convert_tools_for_llm(self, assistant):
        """Test converting MCP tools to LLM format."""
        mcp_tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {
                    "type": "object",
                    "properties": {"param": {"type": "string"}},
                },
            }
        ]

        llm_tools = assistant._convert_tools_for_llm(mcp_tools)

        assert len(llm_tools) == 1
        assert llm_tools[0]["type"] == "function"
        assert llm_tools[0]["function"]["name"] == "test_tool"
        assert llm_tools[0]["function"]["description"] == "A test tool"

    def test_convert_tools_empty(self, assistant):
        """Test converting empty tools list."""
        result = assistant._convert_tools_for_llm([])
        assert result is None

        result = assistant._convert_tools_for_llm(None)
        assert result is None

    def test_clear_conversation(self, assistant):
        """Test clearing conversation history."""
        # Add some messages
        assistant.conversation_history = [
            Message(role=MessageRole.SYSTEM, content="System"),
            Message(role=MessageRole.USER, content="User"),
            Message(role=MessageRole.ASSISTANT, content="Assistant"),
        ]

        assistant.clear_conversation()

        # Should keep only system message
        assert len(assistant.conversation_history) == 1
        assert assistant.conversation_history[0].role == MessageRole.SYSTEM

    @pytest.mark.asyncio
    async def test_shutdown(self, assistant):
        """Test assistant shutdown."""
        assistant.mcp_client.disconnect = AsyncMock()

        await assistant.shutdown()

        assistant.mcp_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_execution_failure(self, assistant):
        """Test handling tool execution failure."""
        # Setup
        await assistant.initialize()

        tools = [
            {
                "name": "failing_tool",
                "description": "A failing tool",
                "parameters": {"type": "object"},
            }
        ]

        tool_call = ToolCall(id="call_456", name="failing_tool", arguments={})

        llm_response = LLMResponse(
            content="I'll try to help.", tool_calls=[tool_call], model="mistral:7b"
        )

        # Tool execution fails
        failed_result = ToolResult(
            tool_call_id="call_456", content="", success=False, error="Tool not found"
        )

        final_response = LLMResponse(
            content="Sorry, I encountered an error.", model="mistral:7b"
        )

        assistant.mcp_client.list_tools = AsyncMock(return_value=tools)
        assistant.llm_service.chat = AsyncMock(
            side_effect=[llm_response, final_response]
        )
        assistant.mcp_client.execute_tool = AsyncMock(return_value=failed_result)

        # Execute
        response = await assistant.process_command("Use failing tool")

        # Verify
        assert response == "Sorry, I encountered an error."
        assistant.mcp_client.execute_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_logging(self, assistant):
        """Test that performance is logged."""
        # Setup
        await assistant.initialize()

        assistant.mcp_client.list_tools = AsyncMock(return_value=[])
        assistant.llm_service.chat = AsyncMock(
            return_value=LLMResponse(content="Response", model="mistral:7b")
        )

        # Execute
        await assistant.process_command("Test")

        # Verify performance logging was called
        assistant.logger.log_performance.assert_called()

    def test_system_prompt_content(self, assistant):
        """Test that system prompt contains expected content."""
        system_prompt = assistant.system_prompt

        assert "Jarvis" in system_prompt
        assert "Iron Man" in system_prompt
        assert "emails" in system_prompt
        assert "calendar" in system_prompt
        assert "concise" in system_prompt

    @pytest.mark.asyncio
    async def test_conversation_history_management(self, assistant):
        """Test that conversation history is properly managed."""
        await assistant.initialize()

        initial_count = len(assistant.conversation_history)

        assistant.mcp_client.list_tools = AsyncMock(return_value=[])
        assistant.llm_service.chat = AsyncMock(
            return_value=LLMResponse(content="Response", model="mistral:7b")
        )

        # Process multiple commands
        await assistant.process_command("First command")
        await assistant.process_command("Second command")

        # Should have: System + (User1 + Assistant1) + (User2 + Assistant2)
        expected_count = initial_count + 4
        assert len(assistant.conversation_history) == expected_count

        # Verify message order and types
        messages = assistant.conversation_history
        assert messages[-4].role == MessageRole.USER
        assert messages[-3].role == MessageRole.ASSISTANT
        assert messages[-2].role == MessageRole.USER
        assert messages[-1].role == MessageRole.ASSISTANT
