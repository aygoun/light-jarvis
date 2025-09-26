"""MCP client for connecting to tools."""

import json
import aiohttp
from typing import Any, Dict, List, Optional

from jarvis_shared.config import MCPConfig
from jarvis_shared.models import ToolCall, ToolResult
from jarvis_shared.logger import get_logger


class MCPClient:
    """Client for interacting with MCP server and tools."""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.logger = get_logger("jarvis.mcp.client")
        self.tools_cache: Dict[str, Dict[str, Any]] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self.base_url = f"http://{config.host}:{config.port}"

    async def connect(self):
        """Connect to MCP server."""
        try:
            self.logger.info(f"🔌 Connecting to MCP server at {self.base_url}")

            # Create HTTP session
            self._session = aiohttp.ClientSession()

            # Test connection with health check
            async with self._session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    self.logger.info(f"✅ Connected to MCP server: {health_data}")

                    # Load available tools
                    await self._load_tools()
                    return True
                else:
                    raise Exception(
                        f"Health check failed with status {response.status}"
                    )

        except Exception as e:
            self.logger.error(f"❌ Failed to connect to MCP server: {e}")
            if self._session:
                await self._session.close()
                self._session = None
            raise

    async def disconnect(self):
        """Disconnect from MCP server."""
        if self._session:
            self.logger.info("🔌 Disconnecting from MCP server")
            await self._session.close()
            self._session = None

    async def _load_tools(self):
        """Load available tools from MCP server."""
        try:
            if not self._session:
                raise Exception("Not connected to MCP server")

            self.logger.info("🔍 Loading tools from MCP server...")

            async with self._session.get(f"{self.base_url}/tools") as response:
                if response.status == 200:
                    tools_data = await response.json()
                    tools_list = tools_data.get("tools", [])

                    # Convert list to dict for easier lookup
                    self.tools_cache = {tool["name"]: tool for tool in tools_list}

                    self.logger.info(
                        f"✅ Loaded {len(self.tools_cache)} tools: {list(self.tools_cache.keys())}"
                    )
                else:
                    raise Exception(f"Failed to load tools, status: {response.status}")

        except Exception as e:
            self.logger.error(f"❌ Failed to load tools: {e}")
            raise

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        if not self._session:
            await self.connect()

        return list(self.tools_cache.values())

    async def execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call."""
        if not self._session:
            await self.connect()

        if tool_call.name not in self.tools_cache:
            return ToolResult(
                tool_call_id=tool_call.id,
                content="",
                success=False,
                error=f"Tool '{tool_call.name}' not found",
            )

        try:
            self.logger.info(
                f"🔧 Executing tool: {tool_call.name} with args: {tool_call.arguments}"
            )

            # Make HTTP request to MCP server
            payload = {
                "id": tool_call.id,
                "name": tool_call.name,
                "arguments": tool_call.arguments,
            }

            async with self._session.post(
                f"{self.base_url}/tools/execute",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:

                if response.status == 200:
                    result_data = await response.json()

                    self.logger.info(f"✅ Tool execution successful: {result_data}")

                    return ToolResult(
                        tool_call_id=tool_call.id,
                        content=json.dumps(result_data),
                        success=True,
                    )
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"❌ Tool execution failed with status {response.status}: {error_text}"
                    )

                    return ToolResult(
                        tool_call_id=tool_call.id,
                        content="",
                        success=False,
                        error=f"HTTP {response.status}: {error_text}",
                    )

        except Exception as e:
            self.logger.error(f"❌ Tool execution error: {e}")
            return ToolResult(
                tool_call_id=tool_call.id, content="", success=False, error=str(e)
            )

    async def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication status from MCP server."""
        try:
            if not self._session:
                await self.connect()

            async with self._session.get(f"{self.base_url}/auth/status") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Failed to get auth status: {response.status}"}

        except Exception as e:
            self.logger.error(f"❌ Failed to get auth status: {e}")
            return {"error": str(e)}

    async def authenticate_google(self) -> Dict[str, Any]:
        """Trigger Google authentication through MCP server."""
        try:
            if not self._session:
                await self.connect()

            self.logger.info("🔐 Triggering Google authentication...")

            async with self._session.post(f"{self.base_url}/auth/google") as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"✅ Google authentication result: {result}")
                    return result
                else:
                    error_text = await response.text()
                    self.logger.error(f"❌ Google authentication failed: {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}

        except Exception as e:
            self.logger.error(f"❌ Google authentication error: {e}")
            return {"error": str(e)}

    async def is_connected(self) -> bool:
        """Check if connected to MCP server."""
        if not self._session:
            return False

        try:
            async with self._session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except:
            return False
