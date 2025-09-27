"""MCP Orchestrator Client for communicating with the MCP Orchestrator server."""

import aiohttp
from typing import Dict, Any, List, Optional
from jarvis_shared.config import MCPConfig
from jarvis_shared.logger import get_logger


class MCPOrchestratorClient:
    """Client for communicating with the MCP Orchestrator server."""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.logger = get_logger("jarvis.mcp.client")
        self.base_url = f"http://{config.host}:{config.port}"
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> None:
        """Connect to the MCP Orchestrator server."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        self.logger.info(f"Connected to MCP Orchestrator at {self.base_url}")

    async def disconnect(self) -> None:
        """Disconnect from the MCP Orchestrator server."""
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("Disconnected from MCP Orchestrator")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.get(f"{self.base_url}/tools") as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("tools", [])

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], tool_call_id: str = "default"
    ) -> Dict[str, Any]:
        """Execute a tool call."""
        if not self.session:
            raise RuntimeError("Client not connected")

        payload = {"id": tool_call_id, "name": tool_name, "arguments": arguments}

        async with self.session.post(
            f"{self.base_url}/tools/execute", json=payload
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def initialize_auth(self) -> Dict[str, Any]:
        """Initialize authentication."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.post(f"{self.base_url}/auth/init") as response:
            response.raise_for_status()
            return await response.json()

    async def authenticate_google(self) -> Dict[str, Any]:
        """Authenticate with Google services."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.post(f"{self.base_url}/auth/google") as response:
            response.raise_for_status()
            return await response.json()

    async def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication status."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.get(f"{self.base_url}/auth/status") as response:
            response.raise_for_status()
            return await response.json()

    async def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.get(f"{self.base_url}/health") as response:
            response.raise_for_status()
            return await response.json()
