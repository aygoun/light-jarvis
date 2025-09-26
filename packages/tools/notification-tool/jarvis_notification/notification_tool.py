"""Notification tool implementation for MCP integration."""

import json
from pathlib import Path
from typing import Dict, Any, List

from jarvis_shared.logger import get_logger
from .notification_client import NotificationClient


class NotificationTool:
    """Notification tool for MCP integration."""

    def __init__(self):
        self.logger = get_logger("jarvis.notification.tool")
        self.client = NotificationClient()

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Notification tool operation."""

        try:
            if tool_name == "send_notification":
                return await self._send_notification(arguments)
            elif tool_name == "schedule_reminder":
                return await self._schedule_reminder(arguments)
            elif tool_name == "cancel_reminder":
                return await self._cancel_reminder(arguments)
            elif tool_name == "list_reminders":
                return await self._list_reminders(arguments)
            else:
                raise ValueError(f"Unknown Notification tool: {tool_name}")

        except Exception as e:
            self.logger.error(f"❌ Notification tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _send_notification(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Send a system notification."""
        title = arguments.get("title", "Jarvis Notification")
        message = arguments.get("message", "")
        timeout = arguments.get("timeout", 10)

        if not message:
            return {"success": False, "error": "Message is required"}

        success = await self.client.send_notification(title, message, timeout)

        if success:
            return {"success": True, "message": "Notification sent successfully"}
        else:
            return {"success": False, "error": "Failed to send notification"}

    async def _schedule_reminder(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a reminder notification."""
        title = arguments.get("title", "Jarvis Reminder")
        message = arguments.get("message", "")
        when = arguments.get("when", "")

        if not message:
            return {"success": False, "error": "Message is required"}

        if not when:
            return {"success": False, "error": "When parameter is required"}

        # Parse when parameter
        remind_at = self._parse_when(when)
        if not remind_at:
            return {
                "success": False,
                "error": f"Could not parse when parameter: {when}",
            }

        # Generate reminder ID
        import uuid

        reminder_id = str(uuid.uuid4())[:8]

        success = await self.client.schedule_reminder(
            reminder_id, title, message, remind_at
        )

        if success:
            return {
                "success": True,
                "reminder_id": reminder_id,
                "message": f"Reminder scheduled for {remind_at.isoformat()}",
                "remind_at": remind_at.isoformat(),
            }
        else:
            return {"success": False, "error": "Failed to schedule reminder"}

    async def _cancel_reminder(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a scheduled reminder."""
        reminder_id = arguments.get("reminder_id", "")

        if not reminder_id:
            return {"success": False, "error": "reminder_id is required"}

        success = await self.client.cancel_reminder(reminder_id)

        if success:
            return {"success": True, "message": f"Reminder {reminder_id} cancelled"}
        else:
            return {"success": False, "error": f"Reminder {reminder_id} not found"}

    async def _list_reminders(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List all scheduled reminders."""
        reminders = self.client.list_reminders()

        return {"success": True, "reminders": reminders, "total": len(reminders)}

    def _parse_when(self, when: str) -> Any:
        """Parse the 'when' parameter into a datetime object."""
        from datetime import datetime, timedelta
        import re

        when = when.lower().strip()

        # Handle relative times
        if when.startswith("in "):
            # Parse "in X minutes/hours/days"
            match = re.match(r"in (\d+)\s*(minute|minutes|hour|hours|day|days)", when)
            if match:
                value = int(match.group(1))
                unit = match.group(2).rstrip("s")  # Remove 's' for singular

                if unit == "minute":
                    return datetime.now() + timedelta(minutes=value)
                elif unit == "hour":
                    return datetime.now() + timedelta(hours=value)
                elif unit == "day":
                    return datetime.now() + timedelta(days=value)

        # Handle specific times
        elif when in ["now", "immediately"]:
            return datetime.now()

        # Handle tomorrow
        elif when == "tomorrow":
            return datetime.now() + timedelta(days=1)

        # Try to parse ISO format
        try:
            return datetime.fromisoformat(when.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Try to parse common formats
        try:
            return datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        try:
            return datetime.strptime(when, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            pass

        return None

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP registration from tools.json."""
        try:
            # Find the tools.json file relative to this file
            current_file = Path(__file__).resolve()
            # Go up: notification_tool.py -> jarvis_notification -> notification-tool -> tools -> packages -> jarvis -> config
            tools_json_path = (
                current_file.parent.parent.parent.parent.parent
                / "config"
                / "tools.json"
            )

            if tools_json_path.exists():
                with open(tools_json_path, "r") as f:
                    tools_config = json.load(f)
                    return tools_config.get("notification", [])
            else:
                self.logger.warning(f"Tools config file not found at {tools_json_path}")
                return []
        except Exception as e:
            self.logger.error(f"Failed to load Notification tool definitions: {e}")
            return []
