"""Tests for Gmail tool."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from jarvis_gmail.gmail_tool import GmailTool
from jarvis_gmail.gmail_client import GmailClient
from jarvis_shared.models import EmailMessage


class TestGmailTool:
    """Test GmailTool class."""

    @pytest.fixture
    def gmail_tool(self, mock_config):
        """Create Gmail tool with mocked dependencies."""
        with (
            patch("jarvis_gmail.gmail_tool.get_logger") as mock_get_logger,
            patch("jarvis_gmail.gmail_tool.GmailClient") as mock_client_class,
        ):

            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            tool = GmailTool(mock_config.google)
            tool.client = mock_client
            tool.logger = mock_logger

            return tool

    @pytest.mark.asyncio
    async def test_execute_gmail_read_emails(self, gmail_tool, sample_email):
        """Test executing gmail_read_emails tool."""
        gmail_tool.client.read_emails = AsyncMock(return_value=[sample_email])

        result = await gmail_tool.execute(
            "gmail_read_emails", {"query": "unread", "max_results": 5}
        )

        assert result["success"] is True
        assert len(result["emails"]) == 1
        assert result["total"] == 1
        assert result["emails"][0]["subject"] == "Test Email"
        assert result["emails"][0]["sender"] == "test@example.com"

        gmail_tool.client.read_emails.assert_called_once_with("unread", 5)

    @pytest.mark.asyncio
    async def test_execute_gmail_send_email(self, gmail_tool):
        """Test executing gmail_send_email tool."""
        gmail_tool.client.send_email = AsyncMock(return_value=True)

        result = await gmail_tool.execute(
            "gmail_send_email",
            {
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "body": "Test body",
            },
        )

        assert result["success"] is True
        assert "Email sent to recipient@example.com" in result["message"]

        gmail_tool.client.send_email.assert_called_once_with(
            "recipient@example.com", "Test Subject", "Test body"
        )

    @pytest.mark.asyncio
    async def test_execute_gmail_send_email_failure(self, gmail_tool):
        """Test gmail_send_email tool failure."""
        gmail_tool.client.send_email = AsyncMock(return_value=False)

        result = await gmail_tool.execute(
            "gmail_send_email",
            {
                "to": "recipient@example.com",
                "subject": "Test Subject",
                "body": "Test body",
            },
        )

        assert result["success"] is False
        assert result["error"] == "Failed to send email"

    @pytest.mark.asyncio
    async def test_execute_gmail_send_email_missing_fields(self, gmail_tool):
        """Test gmail_send_email with missing required fields."""
        result = await gmail_tool.execute(
            "gmail_send_email",
            {
                "to": "recipient@example.com",
                "subject": "Test Subject",
                # Missing 'body' field
            },
        )

        assert result["success"] is False
        assert "Missing required fields" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, gmail_tool):
        """Test executing unknown tool."""
        result = await gmail_tool.execute("unknown_tool", {})

        assert result["success"] is False
        assert "Unknown Gmail tool" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, gmail_tool):
        """Test exception handling in tool execution."""
        gmail_tool.client.read_emails = AsyncMock(side_effect=Exception("Test error"))

        result = await gmail_tool.execute("gmail_read_emails", {})

        assert result["success"] is False
        assert result["error"] == "Test error"
        gmail_tool.logger.error.assert_called()

    def test_get_tool_definitions(self, gmail_tool):
        """Test getting tool definitions."""
        definitions = gmail_tool.get_tool_definitions()

        assert len(definitions) == 2

        # Check gmail_read_emails definition
        read_tool = next(
            tool for tool in definitions if tool["name"] == "gmail_read_emails"
        )
        assert read_tool["description"] == "Read emails from Gmail"
        assert "parameters" in read_tool
        assert "query" in read_tool["parameters"]["properties"]

        # Check gmail_send_email definition
        send_tool = next(
            tool for tool in definitions if tool["name"] == "gmail_send_email"
        )
        assert send_tool["description"] == "Send an email via Gmail"
        assert "required" in send_tool["parameters"]
        assert "to" in send_tool["parameters"]["required"]

    @pytest.mark.asyncio
    async def test_read_emails_with_long_body(self, gmail_tool):
        """Test reading emails with long body text."""
        long_body = "A" * 600  # Longer than 500 character limit

        email = EmailMessage(
            id="email_long",
            subject="Long Email",
            sender="sender@example.com",
            recipients=["user@example.com"],
            body=long_body,
            timestamp=datetime.now(),
        )

        gmail_tool.client.read_emails = AsyncMock(return_value=[email])

        result = await gmail_tool.execute("gmail_read_emails", {})

        assert result["success"] is True
        # Body should be truncated to 500 chars + "..."
        assert len(result["emails"][0]["body"]) == 503
        assert result["emails"][0]["body"].endswith("...")

    @pytest.mark.asyncio
    async def test_read_emails_empty_result(self, gmail_tool):
        """Test reading emails with no results."""
        gmail_tool.client.read_emails = AsyncMock(return_value=[])

        result = await gmail_tool.execute("gmail_read_emails", {"query": "nonexistent"})

        assert result["success"] is True
        assert result["emails"] == []
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_read_emails_default_parameters(self, gmail_tool):
        """Test reading emails with default parameters."""
        gmail_tool.client.read_emails = AsyncMock(return_value=[])

        await gmail_tool.execute("gmail_read_emails", {})

        # Should use default values
        gmail_tool.client.read_emails.assert_called_once_with("", 10)

    @pytest.mark.asyncio
    async def test_send_email_with_all_required_fields(self, gmail_tool):
        """Test sending email with all required fields present."""
        gmail_tool.client.send_email = AsyncMock(return_value=True)

        result = await gmail_tool.execute(
            "gmail_send_email",
            {
                "to": "test@example.com",
                "subject": "Complete Subject",
                "body": "Complete body text",
            },
        )

        assert result["success"] is True
        gmail_tool.client.send_email.assert_called_once_with(
            "test@example.com", "Complete Subject", "Complete body text"
        )

    @pytest.mark.parametrize("missing_field", ["to", "subject", "body"])
    @pytest.mark.asyncio
    async def test_send_email_missing_each_required_field(
        self, gmail_tool, missing_field
    ):
        """Test sending email with each required field missing."""
        complete_args = {
            "to": "test@example.com",
            "subject": "Test Subject",
            "body": "Test body",
        }

        # Remove the field being tested
        del complete_args[missing_field]

        result = await gmail_tool.execute("gmail_send_email", complete_args)

        assert result["success"] is False
        assert "Missing required fields" in result["error"]


class TestGmailClient:
    """Test GmailClient class."""

    @pytest.fixture
    def gmail_client(self, mock_config):
        """Create Gmail client with mocked dependencies."""
        with patch("jarvis_gmail.gmail_client.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            client = GmailClient(mock_config.google)
            client.logger = mock_logger

            return client

    def test_client_initialization(self, gmail_client, mock_config):
        """Test Gmail client initialization."""
        assert gmail_client.config == mock_config.google
        assert gmail_client.service is None
        assert gmail_client.credentials is None
        assert len(gmail_client.SCOPES) == 3

    @pytest.mark.asyncio
    async def test_authenticate_success(self, gmail_client):
        """Test successful authentication."""
        with (
            patch("jarvis_gmail.gmail_client.os.path.exists", return_value=True),
            patch(
                "jarvis_gmail.gmail_client.Credentials.from_authorized_user_file"
            ) as mock_creds,
            patch("jarvis_gmail.gmail_client.build") as mock_build,
        ):

            mock_credentials = Mock()
            mock_credentials.valid = True
            mock_creds.return_value = mock_credentials

            mock_service = Mock()
            mock_build.return_value = mock_service

            result = await gmail_client.authenticate()

            assert result is True
            assert gmail_client.service == mock_service
            assert gmail_client.credentials == mock_credentials

    @pytest.mark.asyncio
    async def test_authenticate_no_credentials_file(self, gmail_client):
        """Test authentication with no credentials file."""
        gmail_client.config.credentials_file = None

        result = await gmail_client.authenticate()

        assert result is False
        gmail_client.logger.error.assert_called()

    def test_parse_email_message(self, gmail_client):
        """Test parsing Gmail API message."""
        gmail_message = {
            "id": "msg_123",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "mimeType": "text/plain",
                "body": {"data": "VGVzdCBib2R5"},  # Base64 for "Test body"
            },
            "internalDate": "1705312200000",  # 2024-01-15 10:30:00
            "labelIds": ["INBOX", "UNREAD"],
        }

        result = gmail_client._parse_email_message(gmail_message)

        assert result.id == "msg_123"
        assert result.subject == "Test Subject"
        assert result.sender == "sender@example.com"
        assert result.recipients == ["recipient@example.com"]
        assert result.body == "Test body"
        assert result.is_read is False  # UNREAD in labels
        assert "INBOX" in result.labels

    def test_extract_body_simple(self, gmail_client):
        """Test extracting body from simple text payload."""
        payload = {
            "mimeType": "text/plain",
            "body": {"data": "SGVsbG8gV29ybGQ="},  # Base64 for "Hello World"
        }

        body = gmail_client._extract_body(payload)
        assert body == "Hello World"

    def test_extract_body_multipart(self, gmail_client):
        """Test extracting body from multipart payload."""
        payload = {
            "parts": [
                {
                    "mimeType": "text/html",
                    "body": {"data": "PGI+SGVsbG88L2I+"},  # HTML content
                },
                {
                    "mimeType": "text/plain",
                    "body": {"data": "SGVsbG8gV29ybGQ="},  # "Hello World"
                },
            ]
        }

        body = gmail_client._extract_body(payload)
        assert body == "Hello World"  # Should prefer plain text

    def test_create_message(self, gmail_client):
        """Test creating email message for sending."""
        result = gmail_client._create_message(
            "recipient@example.com", "Test Subject", "Test body content"
        )

        assert "raw" in result
        assert isinstance(result["raw"], str)

        # Decode and verify content (basic check)
        import base64

        decoded = base64.urlsafe_b64decode(result["raw"]).decode()
        assert "recipient@example.com" in decoded
        assert "Test Subject" in decoded
