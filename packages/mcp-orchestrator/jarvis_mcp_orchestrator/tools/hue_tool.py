"""Hue tool wrapper for MCP Orchestrator."""

from typing import Dict, Any, List, Optional
from jarvis_shared.logger import get_logger
from jarvis_shared.config import HueConfig


class HueTool:
    """Hue tool wrapper for MCP Orchestrator."""

    def __init__(self, config: Optional[HueConfig] = None):
        """Initialize Hue tool wrapper.

        Args:
            config: Hue configuration (uses defaults if None)
        """
        self.config = config or HueConfig()
        self.logger = get_logger("jarvis.mcp.hue")
        self.client: Optional[Any] = None

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Hue tool operation."""
        try:
            # Import here to avoid circular imports
            from jarvis_hue.hue_tool import HueTool as OriginalHueTool

            if not self.client:
                self.client = OriginalHueTool(self.config)

            return await self.client.execute(tool_name, arguments)

        except Exception as e:
            self.logger.error(f"Hue tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP registration."""
        try:
            from jarvis_hue.hue_tool import HueTool as OriginalHueTool

            temp_tool = OriginalHueTool(self.config)
            return temp_tool.get_tool_definitions()
        except Exception as e:
            self.logger.error(f"Failed to get Hue tool definitions: {e}")
            return []
