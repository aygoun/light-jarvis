"""Calendar tool implementation for MCP integration."""

from typing import Dict, Any, List
from datetime import datetime

from jarvis_shared.logger import get_logger
from jarvis_shared.config import GoogleConfig
from .calendar_client import CalendarClient


class CalendarTool:
    """Calendar tool for MCP integration."""

    def __init__(self, config: GoogleConfig):
        self.config = config
        self.logger = get_logger("jarvis.calendar.tool")
        self.client = CalendarClient(config)

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Calendar tool operation."""

        try:
            if tool_name == "calendar_list_events":
                return await self._list_events(arguments)
            elif tool_name == "calendar_create_event":
                return await self._create_event(arguments)
            else:
                raise ValueError(f"Unknown Calendar tool: {tool_name}")

        except Exception as e:
            self.logger.error(f"❌ Calendar tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _list_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List calendar events."""
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        max_results = arguments.get("max_results", 10)

        events = await self.client.list_events(start_date, end_date, max_results)

        # Convert to serializable format
        event_data = []
        for event in events:
            event_data.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "location": event.location,
                    "attendees": event.attendees,
                }
            )

        return {"success": True, "events": event_data, "total": len(event_data)}

    async def _create_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calendar event."""
        title = arguments.get("title")
        start_time = arguments.get("start_time")
        end_time = arguments.get("end_time")
        description = arguments.get("description")
        location = arguments.get("location")

        if not all([title, start_time, end_time]):
            return {
                "success": False,
                "error": "Missing required fields: title, start_time, end_time",
            }

        event_id = await self.client.create_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
        )

        if event_id:
            return {
                "success": True,
                "event_id": event_id,
                "message": f"Event '{title}' created successfully",
                "start_time": start_time,
                "end_time": end_time,
            }
        else:
            return {"success": False, "error": "Failed to create event"}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP registration."""
        return [
            {
                "name": "calendar_list_events",
                "description": "List calendar events",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date (ISO format: YYYY-MM-DDTHH:MM:SS)",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (ISO format: YYYY-MM-DDTHH:MM:SS)",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of events",
                            "default": 10,
                        },
                    },
                },
            },
            {
                "name": "calendar_create_event",
                "description": "Create a new calendar event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Event title"},
                        "start_time": {
                            "type": "string",
                            "description": "Start time (ISO format: YYYY-MM-DDTHH:MM:SS)",
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End time (ISO format: YYYY-MM-DDTHH:MM:SS)",
                        },
                        "description": {
                            "type": "string",
                            "description": "Event description",
                        },
                        "location": {"type": "string", "description": "Event location"},
                    },
                    "required": ["title", "start_time", "end_time"],
                },
            },
        ]
