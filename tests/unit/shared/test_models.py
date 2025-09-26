"""Tests for shared data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from jarvis_shared.models import (
    Message,
    MessageRole,
    ToolCall,
    ToolResult,
    LLMResponse,
    EmailMessage,
    CalendarEvent,
)


class TestMessage:
    """Test Message model."""

    def test_message_creation(self):
        """Test creating a valid message."""
        message = Message(role=MessageRole.USER, content="Hello")

        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert isinstance(message.timestamp, datetime)
        assert message.metadata == {}

    def test_message_with_metadata(self):
        """Test message with metadata."""
        metadata = {"source": "cli", "user_id": "123"}
        message = Message(
            role=MessageRole.ASSISTANT, content="Response", metadata=metadata
        )

        assert message.metadata == metadata

    def test_invalid_role(self):
        """Test invalid message role."""
        with pytest.raises(ValidationError):
            Message(role="invalid_role", content="Hello")


class TestToolCall:
    """Test ToolCall model."""

    def test_tool_call_creation(self):
        """Test creating a valid tool call."""
        tool_call = ToolCall(
            id="call_123", name="gmail_read_emails", arguments={"query": "unread"}
        )

        assert tool_call.id == "call_123"
        assert tool_call.name == "gmail_read_emails"
        assert tool_call.arguments == {"query": "unread"}

    def test_empty_arguments(self):
        """Test tool call with empty arguments."""
        tool_call = ToolCall(id="call_456", name="test_tool", arguments={})
        assert tool_call.arguments == {}


class TestToolResult:
    """Test ToolResult model."""

    def test_successful_result(self):
        """Test successful tool result."""
        result = ToolResult(tool_call_id="call_123", content="Success", success=True)

        assert result.tool_call_id == "call_123"
        assert result.content == "Success"
        assert result.success is True
        assert result.error is None

    def test_failed_result(self):
        """Test failed tool result."""
        result = ToolResult(
            tool_call_id="call_456", content="", success=False, error="Tool not found"
        )

        assert result.success is False
        assert result.error == "Tool not found"


class TestLLMResponse:
    """Test LLMResponse model."""

    def test_simple_response(self):
        """Test simple LLM response without tool calls."""
        response = LLMResponse(content="Hello! How can I help?", model="llama3.2:3b")

        assert response.content == "Hello! How can I help?"
        assert response.model == "llama3.2:3b"
        assert response.tool_calls == []
        assert response.usage == {}

    def test_response_with_tool_calls(self):
        """Test LLM response with tool calls."""
        tool_calls = [ToolCall(id="call_1", name="tool1", arguments={"arg": "value"})]

        response = LLMResponse(
            content="I'll check your emails.",
            tool_calls=tool_calls,
            model="llama3.2:3b",
            usage={"tokens": 100},
        )

        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "tool1"
        assert response.usage == {"tokens": 100}


class TestEmailMessage:
    """Test EmailMessage model."""

    def test_email_creation(self):
        """Test creating a valid email message."""
        timestamp = datetime(2024, 1, 15, 10, 30)
        email = EmailMessage(
            id="email_123",
            subject="Test Subject",
            sender="sender@example.com",
            recipients=["user@example.com"],
            body="Test body",
            timestamp=timestamp,
        )

        assert email.id == "email_123"
        assert email.subject == "Test Subject"
        assert email.sender == "sender@example.com"
        assert email.recipients == ["user@example.com"]
        assert email.body == "Test body"
        assert email.timestamp == timestamp
        assert email.is_read is False
        assert email.labels == []

    def test_email_with_labels(self):
        """Test email with labels."""
        email = EmailMessage(
            id="email_456",
            subject="Important",
            sender="boss@example.com",
            recipients=["user@example.com"],
            body="Important message",
            timestamp=datetime.now(),
            is_read=True,
            labels=["INBOX", "IMPORTANT"],
        )

        assert email.is_read is True
        assert email.labels == ["INBOX", "IMPORTANT"]


class TestCalendarEvent:
    """Test CalendarEvent model."""

    def test_event_creation(self):
        """Test creating a valid calendar event."""
        start_time = datetime(2024, 1, 16, 14, 0)
        end_time = datetime(2024, 1, 16, 15, 0)

        event = CalendarEvent(
            id="event_123",
            title="Team Meeting",
            start_time=start_time,
            end_time=end_time,
        )

        assert event.id == "event_123"
        assert event.title == "Team Meeting"
        assert event.start_time == start_time
        assert event.end_time == end_time
        assert event.description is None
        assert event.location is None
        assert event.attendees == []
        assert event.reminders == []

    def test_event_with_all_fields(self):
        """Test event with all optional fields."""
        start_time = datetime(2024, 1, 16, 14, 0)
        end_time = datetime(2024, 1, 16, 15, 0)
        attendees = ["user1@example.com", "user2@example.com"]
        reminders = [15, 5]  # 15 and 5 minutes before

        event = CalendarEvent(
            id="event_456",
            title="Important Meeting",
            description="Quarterly review",
            start_time=start_time,
            end_time=end_time,
            location="Conference Room A",
            attendees=attendees,
            reminders=reminders,
        )

        assert event.description == "Quarterly review"
        assert event.location == "Conference Room A"
        assert event.attendees == attendees
        assert event.reminders == reminders

    def test_invalid_event_missing_required(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError):
            CalendarEvent(
                id="event_invalid",
                title="Meeting",
                # Missing required start_time and end_time
            )
