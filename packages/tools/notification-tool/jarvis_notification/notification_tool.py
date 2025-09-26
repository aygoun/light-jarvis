"""Notification tool implementation for MCP integration."""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid

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
        when = arguments.get(
            "when", ""
        )  # e.g., "in 5 minutes", "at 2:30 PM", "2024-01-15T14:30:00"

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

    def _parse_when(self, when: str) -> datetime:
        """Parse when string into datetime."""
        try:
            when = when.lower().strip()
            now = datetime.now()

            # Handle "in X minutes/hours/days"
            if when.startswith("in "):
                parts = when[3:].split()
                if len(parts) >= 2:
                    try:
                        amount = int(parts[0])
                        unit = parts[1].lower()

                        if unit.startswith("minute"):
                            return now + timedelta(minutes=amount)
                        elif unit.startswith("hour"):
                            return now + timedelta(hours=amount)
                        elif unit.startswith("day"):
                            return now + timedelta(days=amount)
                        elif unit.startswith("second"):
                            return now + timedelta(seconds=amount)
                    except ValueError:
                        pass

            # Handle ISO format
            if "T" in when or "-" in when:
                try:
                    # Try ISO format
                    return datetime.fromisoformat(when.replace("Z", "+00:00"))
                except ValueError:
                    pass

            # Handle relative times like "tomorrow", "next week"
            if "tomorrow" in when:
                return now + timedelta(days=1)
            elif "next week" in when:
                return now + timedelta(weeks=1)

            return datetime.now()

        except Exception as e:
            self.logger.error(f"❌ Failed to parse when parameter: {e}")
            return datetime.now()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP registration."""
        return [
            {
                "name": "send_notification",
                "description": "Send a system notification",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Notification title",
                            "default": "Jarvis Notification",
                        },
                        "message": {
                            "type": "string",
                            "description": "Notification message",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Notification timeout in seconds",
                            "default": 10,
                        },
                    },
                    "required": ["message"],
                },
            },
            {
                "name": "schedule_reminder",
                "description": "Schedule a reminder notification",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Reminder title",
                            "default": "Jarvis Reminder",
                        },
                        "message": {
                            "type": "string",
                            "description": "Reminder message",
                        },
                        "when": {
                            "type": "string",
                            "description": "When to remind (e.g., 'in 5 minutes', 'tomorrow', '2024-01-15T14:30:00')",
                        },
                    },
                    "required": ["message", "when"],
                },
            },
            {
                "name": "cancel_reminder",
                "description": "Cancel a scheduled reminder",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reminder_id": {
                            "type": "string",
                            "description": "ID of the reminder to cancel",
                        },
                    },
                    "required": ["reminder_id"],
                },
            },
            {
                "name": "list_reminders",
                "description": "List all scheduled reminders",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]
