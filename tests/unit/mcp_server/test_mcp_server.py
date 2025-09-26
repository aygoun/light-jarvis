"""Tests for MCP Server."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from jarvis_mcp.server import MCPServer, ToolCall, ToolResult


class TestMCPServer:
    """Test MCPServer class."""

    @pytest.fixture
    def mcp_server(self, mock_config):
        """Create MCP server with mocked dependencies."""
        with patch("jarvis_mcp.server.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            server = MCPServer(mock_config.mcp)
            server.logger = mock_logger

            return server

    @pytest.fixture
    def test_client(self, mcp_server):
        """Create test client for FastAPI app."""
        return TestClient(mcp_server.app)

    def test_server_initialization(self, mcp_server, mock_config):
        """Test server initialization."""
        assert mcp_server.config == mock_config.mcp
        assert mcp_server.tools_registry == {}
        assert mcp_server.app.title == "Jarvis MCP Server"

    def test_register_tool(self, mcp_server):
        """Test registering a tool."""
        tool_config = {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {"type": "object"},
        }

        mcp_server.register_tool(tool_config)

        assert "test_tool" in mcp_server.tools_registry
        assert mcp_server.tools_registry["test_tool"] == tool_config
        mcp_server.logger.info.assert_called_with("🔧 Registered tool: test_tool")

    def test_list_tools_endpoint(self, test_client, mcp_server):
        """Test the /tools endpoint."""
        # Register a test tool
        tool_config = {"name": "test_tool", "description": "A test tool"}
        mcp_server.register_tool(tool_config)

        response = test_client.get("/tools")

        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "test_tool"

    def test_health_endpoint(self, test_client, mcp_server):
        """Test the /health endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["tools_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_tool_endpoint_success(self, test_client, mcp_server):
        """Test successful tool execution."""
        # Register a tool
        tool_config = {"name": "gmail_read_emails", "description": "Read emails"}
        mcp_server.register_tool(tool_config)

        # Execute tool
        tool_call_data = {
            "id": "call_123",
            "name": "gmail_read_emails",
            "arguments": {"query": "unread"},
        }

        response = test_client.post("/tools/execute", json=tool_call_data)

        assert response.status_code == 200
        data = response.json()
        assert data["tool_call_id"] == "call_123"
        assert data["success"] is True
        assert "emails" in data["content"]

    def test_execute_tool_endpoint_not_found(self, test_client):
        """Test tool execution with unknown tool."""
        tool_call_data = {"id": "call_456", "name": "unknown_tool", "arguments": {}}

        response = test_client.post("/tools/execute", json=tool_call_data)

        assert response.status_code == 200  # Returns 200 with error in response
        data = response.json()
        assert data["tool_call_id"] == "call_456"
        assert data["success"] is False
        assert "not found" in data["error"]

    @pytest.mark.asyncio
    async def test_simulate_gmail_read_emails(self, mcp_server):
        """Test simulating Gmail read emails."""
        result = await mcp_server._simulate_tool_execution(
            "gmail_read_emails", {"query": "unread", "max_results": 5}
        )

        assert "emails" in result
        assert "total" in result
        assert isinstance(result["emails"], list)
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_simulate_gmail_send_email(self, mcp_server):
        """Test simulating Gmail send email."""
        result = await mcp_server._simulate_tool_execution(
            "gmail_send_email",
            {"to": "test@example.com", "subject": "Test", "body": "Test message"},
        )

        assert "message_id" in result
        assert "status" in result
        assert result["status"] == "sent"

    @pytest.mark.asyncio
    async def test_simulate_calendar_list_events(self, mcp_server):
        """Test simulating calendar list events."""
        result = await mcp_server._simulate_tool_execution(
            "calendar_list_events", {"start_date": "2024-01-15", "max_results": 10}
        )

        assert "events" in result
        assert "total" in result
        assert isinstance(result["events"], list)
        assert result["total"] == 1

    @pytest.mark.asyncio
    async def test_simulate_calendar_create_event(self, mcp_server):
        """Test simulating calendar create event."""
        result = await mcp_server._simulate_tool_execution(
            "calendar_create_event",
            {
                "title": "Test Meeting",
                "start_time": "2024-01-16T14:00:00Z",
                "end_time": "2024-01-16T15:00:00Z",
            },
        )

        assert "event_id" in result
        assert "status" in result
        assert result["status"] == "created"
        assert result["title"] == "Test Meeting"

    @pytest.mark.asyncio
    async def test_simulate_unknown_tool(self, mcp_server):
        """Test simulating unknown tool."""
        result = await mcp_server._simulate_tool_execution(
            "unknown_tool", {"param": "value"}
        )

        assert result["status"] == "executed"
        assert result["tool"] == "unknown_tool"
        assert result["arguments"] == {"param": "value"}

    def test_register_default_tools(self, mcp_server):
        """Test that default tools are registered."""
        mcp_server._register_default_tools()

        expected_tools = [
            "gmail_read_emails",
            "gmail_send_email",
            "calendar_list_events",
            "calendar_create_event",
        ]

        for tool_name in expected_tools:
            assert tool_name in mcp_server.tools_registry

        # Check tool structure
        gmail_tool = mcp_server.tools_registry["gmail_read_emails"]
        assert gmail_tool["description"] == "Read emails from Gmail"
        assert "parameters" in gmail_tool

    @pytest.mark.asyncio
    async def test_start_server_mock(self, mcp_server):
        """Test server startup (mocked)."""
        with (
            patch("uvicorn.Config") as mock_config,
            patch("uvicorn.Server") as mock_server_class,
        ):

            mock_server = Mock()
            mock_server_class.return_value = mock_server
            mock_server.serve = AsyncMock()

            await mcp_server.start_server()

            mock_config.assert_called_once()
            mock_server_class.assert_called_once()
            mock_server.serve.assert_called_once()
            mcp_server.logger.info.assert_called()

    def test_tool_call_model(self):
        """Test ToolCall pydantic model."""
        tool_call = ToolCall(
            id="call_123", name="test_tool", arguments={"param": "value"}
        )

        assert tool_call.id == "call_123"
        assert tool_call.name == "test_tool"
        assert tool_call.arguments == {"param": "value"}

    def test_tool_result_model(self):
        """Test ToolResult pydantic model."""
        result = ToolResult(tool_call_id="call_123", content="Success", success=True)

        assert result.tool_call_id == "call_123"
        assert result.content == "Success"
        assert result.success is True
        assert result.error is None

    def test_tool_result_with_error(self):
        """Test ToolResult with error."""
        result = ToolResult(
            tool_call_id="call_456",
            content="",
            success=False,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.error == "Something went wrong"

    def test_invalid_tool_call_json(self, test_client):
        """Test invalid JSON in tool call."""
        response = test_client.post(
            "/tools/execute",
            json={
                "id": "call_123",
                "name": "test_tool",
                # Missing required 'arguments' field
            },
        )

        assert response.status_code == 422  # Validation error

    def test_tools_endpoint_empty(self, test_client):
        """Test tools endpoint with no tools registered."""
        response = test_client.get("/tools")

        assert response.status_code == 200
        data = response.json()
        assert data["tools"] == []

    def test_multiple_tool_registration(self, mcp_server):
        """Test registering multiple tools."""
        tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"},
            {"name": "tool3", "description": "Third tool"},
        ]

        for tool in tools:
            mcp_server.register_tool(tool)

        assert len(mcp_server.tools_registry) == 3
        for tool in tools:
            assert tool["name"] in mcp_server.tools_registry
