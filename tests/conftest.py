"""Pytest configuration and fixtures for Jarvis tests."""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock

import pytest

# Add packages to path for testing
project_root = Path(__file__).parent.parent
for package_dir in ["shared", "core", "llm-service", "mcp-server"]:
    sys.path.insert(0, str(project_root / "packages" / package_dir))

# Add tool packages to path
for tool_dir in ["gmail-tool", "calendar-tool", "notification-tool"]:
    sys.path.insert(0, str(project_root / "packages" / "tools" / tool_dir))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Mock configuration for testing using TOML values."""
    from jarvis_shared.config import (
        JarvisConfig,
        OllamaConfig,
        MCPConfig,
        GoogleConfig,
        GeneralConfig,
        LoggingConfig,
    )

    config = Mock(spec=JarvisConfig)

    # Ollama configuration from TOML
    config.ollama = Mock(spec=OllamaConfig)
    config.ollama.host = "http://localhost:11434"
    config.ollama.model = "llama3.2:3b"
    config.ollama.temperature = 0.1
    config.ollama.timeout = 120

    # MCP configuration from TOML
    config.mcp = Mock(spec=MCPConfig)
    config.mcp.host = "localhost"
    config.mcp.port = 3000  # Updated to match TOML
    config.mcp.timeout = 30

    # Google configuration from TOML
    config.google = Mock(spec=GoogleConfig)
    config.google.credentials_file = "~/.jarvis/google_credentials.json"
    config.google.token_file = "~/.jarvis/google_token.json"
    config.google.scopes = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events",
    ]

    # General configuration from TOML
    config.general = Mock(spec=GeneralConfig)
    config.general.debug = False
    config.general.log_level = "DEBUG"

    # Logging configuration from TOML
    config.logging = Mock(spec=LoggingConfig)
    config.logging.level = "INFO"
    config.logging.dir = "./logs"
    config.logging.console = False
    config.logging.file = True
    config.logging.rich = True
    config.logging.max_size = 10485760
    config.logging.backup_count = 5
    config.logging.date_format = "%Y-%m-%d %H:%M:%S"

    return config


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    logger.exception = Mock()
    logger.log_performance = Mock()
    logger.log_tool_execution = Mock()
    logger.log_api_call = Mock()
    return logger


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing."""
    client = AsyncMock()
    client.chat = AsyncMock()
    client.chat_stream = AsyncMock()
    client.list_models = Mock(return_value=["llama3.2:3b", "llama3.1:8b"])
    client.pull_model = Mock(return_value=True)
    return client


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.list_tools = AsyncMock(
        return_value=[
            {
                "name": "gmail_read_emails",
                "description": "Read emails from Gmail",
                "parameters": {"type": "object", "properties": {}},
            }
        ]
    )
    client.execute_tool = AsyncMock()
    return client


@pytest.fixture
def sample_messages():
    """Sample messages for testing."""
    from jarvis_shared.models import Message, MessageRole

    return [
        Message(role=MessageRole.SYSTEM, content="You are Jarvis AI assistant."),
        Message(role=MessageRole.USER, content="Hello, how are you?"),
        Message(role=MessageRole.ASSISTANT, content="I'm doing well, thank you!"),
    ]


@pytest.fixture
def sample_llm_response():
    """Sample LLM response for testing."""
    from jarvis_shared.models import LLMResponse, ToolCall

    return LLMResponse(
        content="Hello! I can help you with emails and calendar.",
        tool_calls=[
            ToolCall(
                id="call_123",
                name="gmail_read_emails",
                arguments={"query": "unread", "max_results": 5},
            )
        ],
        model="llama3.2:3b",
        usage={"prompt_tokens": 50, "completion_tokens": 25},
    )


@pytest.fixture
def sample_email():
    """Sample email for testing."""
    from jarvis_shared.models import EmailMessage
    from datetime import datetime

    return EmailMessage(
        id="email_123",
        subject="Test Email",
        sender="test@example.com",
        recipients=["user@example.com"],
        body="This is a test email.",
        timestamp=datetime(2024, 1, 15, 10, 30),
        is_read=False,
        labels=["INBOX", "UNREAD"],
    )


@pytest.fixture
def sample_calendar_event():
    """Sample calendar event for testing."""
    from jarvis_shared.models import CalendarEvent
    from datetime import datetime

    return CalendarEvent(
        id="event_123",
        title="Test Meeting",
        description="A test meeting",
        start_time=datetime(2024, 1, 16, 14, 0),
        end_time=datetime(2024, 1, 16, 15, 0),
        location="Conference Room A",
        attendees=["user@example.com", "colleague@example.com"],
        reminders=[15, 5],  # 15 and 5 minutes before
    )


@pytest.fixture
def temp_log_dir(tmp_path):
    """Temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    # Store original values
    original_env = {}
    jarvis_vars = [key for key in os.environ.keys() if key.startswith("JARVIS_")]

    for var in jarvis_vars:
        original_env[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def mock_google_service():
    """Mock Google API service for testing."""
    service = Mock()

    # Gmail service mocks
    service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "msg_123"}]
    }
    service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "msg_123",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Test Email"},
                {"name": "From", "value": "test@example.com"},
                {"name": "To", "value": "user@example.com"},
            ],
            "mimeType": "text/plain",
            "body": {
                "data": "VGhpcyBpcyBhIHRlc3QgZW1haWwu"
            },  # Base64 encoded "This is a test email."
        },
        "internalDate": "1705312200000",  # 2024-01-15 10:30:00
        "labelIds": ["INBOX", "UNREAD"],
    }

    service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
        "id": "sent_123"
    }

    # Calendar service mocks
    service.events.return_value.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "event_123",
                "summary": "Test Meeting",
                "description": "A test meeting",
                "start": {"dateTime": "2024-01-16T14:00:00Z"},
                "end": {"dateTime": "2024-01-16T15:00:00Z"},
                "location": "Conference Room A",
                "attendees": [
                    {"email": "user@example.com"},
                    {"email": "colleague@example.com"},
                ],
            }
        ]
    }

    service.events.return_value.insert.return_value.execute.return_value = {
        "id": "created_456"
    }

    return service


@pytest.fixture
async def async_mock_stream():
    """Mock async generator for streaming responses."""

    async def mock_generator():
        tokens = ["Hello", " there", "! How", " can I", " help you", " today?"]
        for token in tokens:
            yield token

    return mock_generator()
