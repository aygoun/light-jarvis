"""Calendar tool wrapper for MCP Orchestrator."""

from typing import Dict, Any, List, Optional
from jarvis_shared.config import GoogleConfig
from jarvis_shared.logger import get_logger


class CalendarTool:
    """Calendar tool wrapper for MCP Orchestrator."""

    def __init__(self, config: Optional[GoogleConfig] = None):
        self.config = config
        self.logger = get_logger("jarvis.mcp.calendar")
        self.client: Optional[Any] = None

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Calendar tool operation."""
        try:
            # Import here to avoid circular imports
            from jarvis_calendar.calendar_tool import (
                CalendarTool as OriginalCalendarTool,
            )

            if not self.client:
                self.client = OriginalCalendarTool(self.config)

            return await self.client.execute(tool_name, arguments)

        except Exception as e:
            self.logger.error(f"Calendar tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP registration."""
        try:
            from jarvis_calendar.calendar_tool import (
                CalendarTool as OriginalCalendarTool,
            )

            temp_tool = OriginalCalendarTool(self.config)
            return temp_tool.get_tool_definitions()
        except Exception as e:
            self.logger.error(f"Failed to get Calendar tool definitions: {e}")
            return []
