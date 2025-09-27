"""Notification tool wrapper for MCP Orchestrator."""

from typing import Dict, Any, List, Optional
from jarvis_shared.logger import get_logger


class NotificationTool:
    """Notification tool wrapper for MCP Orchestrator."""

    def __init__(self):
        self.logger = get_logger("jarvis.mcp.notification")
        self.client: Optional[Any] = None

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Notification tool operation."""
        try:
            # Import here to avoid circular imports
            from jarvis_notification.notification_tool import (
                NotificationTool as OriginalNotificationTool,
            )

            if not self.client:
                self.client = OriginalNotificationTool()

            return await self.client.execute(tool_name, arguments)

        except Exception as e:
            self.logger.error(f"Notification tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP registration."""
        try:
            from jarvis_notification.notification_tool import (
                NotificationTool as OriginalNotificationTool,
            )

            temp_tool = OriginalNotificationTool()
            return temp_tool.get_tool_definitions()
        except Exception as e:
            self.logger.error(f"Failed to get Notification tool definitions: {e}")
            return []
