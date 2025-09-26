"""Shared data models for Jarvis."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message roles for LLM conversations."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    """A message in the conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Represents a tool call from the LLM."""

    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Result from executing a tool."""

    tool_call_id: str
    content: str
    success: bool
    error: Optional[str] = None


class LLMResponse(BaseModel):
    """Response from the LLM."""

    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    model: str
    usage: Dict[str, Any] = Field(default_factory=dict)


class EmailMessage(BaseModel):
    """Email message model."""

    id: str
    subject: str
    sender: str
    recipients: List[str]
    body: str
    timestamp: datetime
    is_read: bool = False
    labels: List[str] = Field(default_factory=list)


class CalendarEvent(BaseModel):
    """Calendar event model."""

    id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    reminders: List[int] = Field(default_factory=list)  # minutes before event
