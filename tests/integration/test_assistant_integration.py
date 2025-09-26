"""Integration tests for Jarvis Assistant."""

import pytest
from unittest.mock import AsyncMock, patch

from jarvis_shared.models import LLMResponse, ToolCall, ToolResult
from jarvis_core.assistant import JarvisAssistant


@pytest.mark.integration
class TestJarvisAssistantIntegration:
    """Integration tests for JarvisAssistant with real-like components."""

    @pytest.fixture
    async def integrated_assistant(self, mock_config):
        """Create assistant with integrated but mocked services."""

        # Mock the LLM service with realistic responses
        mock_llm_service = AsyncMock()
        mock_llm_service.chat = AsyncMock()
        mock_llm_service.chat_stream = AsyncMock()

        # Mock the MCP client with realistic tool interactions
        mock_mcp_client = AsyncMock()
        mock_mcp_client.connect = AsyncMock()
        mock_mcp_client.disconnect = AsyncMock()
        mock_mcp_client.list_tools = AsyncMock()
        mock_mcp_client.execute_tool = AsyncMock()

        with (
            patch("jarvis_core.assistant.LLMService", return_value=mock_llm_service),
            patch("jarvis_core.assistant.MCPClient", return_value=mock_mcp_client),
            patch("jarvis_core.assistant.get_logger"),
        ):

            assistant = JarvisAssistant(mock_config)
            await assistant.initialize()

            return assistant

    @pytest.mark.asyncio
    async def test_email_workflow_integration(self, integrated_assistant):
        """Test complete email reading workflow."""

        # Setup tools
        tools = [
            {
                "name": "gmail_read_emails",
                "description": "Read emails from Gmail",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer"},
                    },
                },
            }
        ]

        # Setup LLM response with tool call
        tool_call = ToolCall(
            id="call_email_123",
            name="gmail_read_emails",
            arguments={"query": "unread", "max_results": 5},
        )

        llm_response = LLMResponse(
            content="I'll check your unread emails now.",
            tool_calls=[tool_call],
            model="llama3.2:3b",
        )

        # Setup tool execution result
        tool_result = ToolResult(
            tool_call_id="call_email_123",
            content='{"emails": [{"subject": "Important Meeting", "sender": "boss@company.com", "body": "Please join the meeting at 2 PM"}], "total": 1}',
            success=True,
        )

        # Setup final LLM response
        final_response = LLMResponse(
            content="You have 1 unread email from boss@company.com with subject 'Important Meeting' about joining a meeting at 2 PM.",
            model="llama3.2:3b",
        )

        # Configure mocks
        integrated_assistant.mcp_client.list_tools.return_value = tools
        integrated_assistant.llm_service.chat.side_effect = [
            llm_response,
            final_response,
        ]
        integrated_assistant.mcp_client.execute_tool.return_value = tool_result

        # Execute
        response = await integrated_assistant.process_command("Check my unread emails")

        # Verify
        assert "boss@company.com" in response
        assert "Important Meeting" in response
        assert "2 PM" in response

        # Verify tool was called with correct arguments
        integrated_assistant.mcp_client.execute_tool.assert_called_once_with(tool_call)

        # Verify conversation history
        assert (
            len(integrated_assistant.conversation_history) == 5
        )  # System + User + Assistant + Tool + Assistant

    @pytest.mark.asyncio
    async def test_calendar_workflow_integration(self, integrated_assistant):
        """Test complete calendar event creation workflow."""

        # Setup tools
        tools = [
            {
                "name": "calendar_create_event",
                "description": "Create a calendar event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    },
                    "required": ["title", "start_time", "end_time"],
                },
            }
        ]

        # Setup LLM response with tool call
        tool_call = ToolCall(
            id="call_calendar_456",
            name="calendar_create_event",
            arguments={
                "title": "Team Standup",
                "start_time": "2024-01-16T09:00:00Z",
                "end_time": "2024-01-16T09:30:00Z",
            },
        )

        llm_response = LLMResponse(
            content="I'll create the team standup meeting for you.",
            tool_calls=[tool_call],
            model="llama3.2:3b",
        )

        # Setup tool execution result
        tool_result = ToolResult(
            tool_call_id="call_calendar_456",
            content='{"event_id": "event_789", "status": "created", "title": "Team Standup"}',
            success=True,
        )

        # Setup final response
        final_response = LLMResponse(
            content="I've successfully created the 'Team Standup' meeting for January 16th from 9:00 AM to 9:30 AM.",
            model="llama3.2:3b",
        )

        # Configure mocks
        integrated_assistant.mcp_client.list_tools.return_value = tools
        integrated_assistant.llm_service.chat.side_effect = [
            llm_response,
            final_response,
        ]
        integrated_assistant.mcp_client.execute_tool.return_value = tool_result

        # Execute
        response = await integrated_assistant.process_command(
            "Create a team standup meeting for tomorrow at 9 AM"
        )

        # Verify
        assert "Team Standup" in response
        assert "January 16th" in response
        assert "9:00 AM" in response

        # Verify tool execution
        integrated_assistant.mcp_client.execute_tool.assert_called_once_with(tool_call)

    @pytest.mark.asyncio
    async def test_streaming_integration(self, integrated_assistant):
        """Test streaming response integration."""

        # Setup for streaming without tools
        integrated_assistant.mcp_client.list_tools.return_value = []

        # Create streaming response
        async def mock_stream():
            tokens = ["Hello", "! I'm", " Jarvis", ", your", " AI", " assistant", "."]
            for token in tokens:
                yield token

        integrated_assistant.llm_service.chat_stream.return_value = mock_stream()

        # Execute streaming
        full_response = ""
        async for token in integrated_assistant.process_command_stream("Hello"):
            full_response += token

        # Verify
        assert full_response == "Hello! I'm Jarvis, your AI assistant."

        # Check conversation history was updated
        assert len(integrated_assistant.conversation_history) == 3
        assert integrated_assistant.conversation_history[-1].content == full_response

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, integrated_assistant):
        """Test error handling in integrated workflow."""

        # Setup tools
        tools = [
            {
                "name": "failing_tool",
                "description": "A tool that fails",
                "parameters": {"type": "object"},
            }
        ]

        # Setup LLM response with failing tool call
        tool_call = ToolCall(id="call_fail_789", name="failing_tool", arguments={})

        llm_response = LLMResponse(
            content="I'll try to help with that.",
            tool_calls=[tool_call],
            model="llama3.2:3b",
        )

        # Setup failed tool result
        failed_result = ToolResult(
            tool_call_id="call_fail_789",
            content="",
            success=False,
            error="Tool execution failed: Connection timeout",
        )

        # Setup recovery response
        recovery_response = LLMResponse(
            content="I'm sorry, I encountered an error while trying to help. The service appears to be temporarily unavailable.",
            model="llama3.2:3b",
        )

        # Configure mocks
        integrated_assistant.mcp_client.list_tools.return_value = tools
        integrated_assistant.llm_service.chat.side_effect = [
            llm_response,
            recovery_response,
        ]
        integrated_assistant.mcp_client.execute_tool.return_value = failed_result

        # Execute
        response = await integrated_assistant.process_command("Use the failing tool")

        # Verify graceful error handling
        assert "sorry" in response.lower()
        assert "error" in response.lower()

        # Verify tool was attempted
        integrated_assistant.mcp_client.execute_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_multi_tool_workflow(self, integrated_assistant):
        """Test workflow with multiple tool calls."""

        # Setup multiple tools
        tools = [
            {
                "name": "gmail_read_emails",
                "description": "Read emails",
                "parameters": {"type": "object"},
            },
            {
                "name": "calendar_list_events",
                "description": "List events",
                "parameters": {"type": "object"},
            },
        ]

        # Setup LLM response with multiple tool calls
        tool_calls = [
            ToolCall(
                id="call_1", name="gmail_read_emails", arguments={"query": "today"}
            ),
            ToolCall(
                id="call_2",
                name="calendar_list_events",
                arguments={"start_date": "2024-01-15"},
            ),
        ]

        llm_response = LLMResponse(
            content="I'll check both your emails and calendar.",
            tool_calls=tool_calls,
            model="llama3.2:3b",
        )

        # Setup tool results
        email_result = ToolResult(
            tool_call_id="call_1", content='{"emails": [], "total": 0}', success=True
        )

        calendar_result = ToolResult(
            tool_call_id="call_2",
            content='{"events": [{"title": "Meeting"}], "total": 1}',
            success=True,
        )

        # Setup final response
        final_response = LLMResponse(
            content="You have no new emails today, but you have 1 calendar event: a Meeting.",
            model="llama3.2:3b",
        )

        # Configure mocks
        integrated_assistant.mcp_client.list_tools.return_value = tools
        integrated_assistant.llm_service.chat.side_effect = [
            llm_response,
            final_response,
        ]
        integrated_assistant.mcp_client.execute_tool.side_effect = [
            email_result,
            calendar_result,
        ]

        # Execute
        response = await integrated_assistant.process_command(
            "What's my schedule today?"
        )

        # Verify
        assert "no new emails" in response.lower()
        assert "Meeting" in response

        # Verify both tools were called
        assert integrated_assistant.mcp_client.execute_tool.call_count == 2

    @pytest.mark.asyncio
    async def test_conversation_persistence(self, integrated_assistant):
        """Test that conversation context is maintained across multiple interactions."""

        # First interaction
        integrated_assistant.mcp_client.list_tools.return_value = []
        integrated_assistant.llm_service.chat.return_value = LLMResponse(
            content="Hello! I'm Jarvis.", model="llama3.2:3b"
        )

        response1 = await integrated_assistant.process_command("Hello")

        # Second interaction that references first
        integrated_assistant.llm_service.chat.return_value = LLMResponse(
            content="Yes, I just introduced myself as Jarvis, your AI assistant.",
            model="llama3.2:3b",
        )

        response2 = await integrated_assistant.process_command(
            "What did you just say your name was?"
        )

        # Verify responses
        assert "Jarvis" in response1
        assert "Jarvis" in response2
        assert "just introduced myself" in response2

        # Verify conversation history contains both interactions
        assert (
            len(integrated_assistant.conversation_history) == 5
        )  # System + User1 + Asst1 + User2 + Asst2

        # Verify the LLM received the full conversation context
        second_call_args = integrated_assistant.llm_service.chat.call_args_list[1]
        messages_sent = second_call_args[0][0]  # First positional argument
        assert len(messages_sent) == 4  # System + User1 + Asst1 + User2
