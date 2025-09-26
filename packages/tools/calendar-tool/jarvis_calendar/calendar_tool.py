"""Calendar tool implementation for MCP integration."""

import json
from pathlib import Path
from typing import Dict, Any, List

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
                self.logger.info(f"🔍 Listing events with arguments: {arguments}")
                return await self._list_events(arguments)
            elif tool_name == "calendar_create_event":
                self.logger.info(f"🔍 Creating event with arguments: {arguments}")
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

        self.logger.info(
            f"🔍 Listing events with start_date: {start_date}, end_date: {end_date}, max_results: {max_results}"
        )

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
            title=str(title),
            start_time=str(start_time),
            end_time=str(end_time),
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
        """Get tool definitions for MCP registration from tools.json."""
        try:
            # Find the tools.json file relative to this file
            current_file = Path(__file__).resolve()
            # Go up: calendar_tool.py -> jarvis_calendar -> calendar-tool -> tools -> packages -> jarvis -> config
            tools_json_path = (
                current_file.parent.parent.parent.parent.parent
                / "config"
                / "tools.json"
            )

            if tools_json_path.exists():
                with open(tools_json_path, "r") as f:
                    tools_config = json.load(f)
                    return tools_config.get("calendar", [])
            else:
                self.logger.warning(f"Tools config file not found at {tools_json_path}")
                return []
        except Exception as e:
            self.logger.error(f"Failed to load Calendar tool definitions: {e}")
            return []
