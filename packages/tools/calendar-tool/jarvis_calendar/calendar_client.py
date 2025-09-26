"""Google Calendar API client for calendar operations."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any


from jarvis_shared.models import CalendarEvent
from jarvis_shared.logger import get_logger
from jarvis_shared.config import GoogleConfig


class CalendarClient:
    """Client for Google Calendar API operations."""

    def __init__(self, config: GoogleConfig):
        self.config = config
        self.logger = get_logger("jarvis.calendar.client")
        self.service = None
        self.credentials = None

    def is_authenticated(self) -> bool:
        """Check if the Calendar service is authenticated and ready to use."""
        return self.service is not None

    async def list_events(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 10,
    ) -> List[CalendarEvent]:
        """List calendar events."""
        if not self.is_authenticated():
            self.logger.error("❌ Calendar service not authenticated")
            self.logger.info(
                "   Ensure GoogleAuthManager has authenticated the service"
            )
            return []

        try:
            # Default to next 7 days if no dates specified
            if not start_date:
                start_time = datetime.utcnow()
            else:
                start_time = datetime.fromisoformat(start_date)

            if not end_date:
                end_time = start_time + timedelta(days=7)
            else:
                end_time = datetime.fromisoformat(end_date)

            self.logger.info(f"📅 Listing events from {start_time} to {end_time}")

            if not self.service:
                raise RuntimeError("Calendar service not authenticated")

            self.logger.info(f"🔍 Calendar service: {self.service}")
            # Get events
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_time.isoformat() + "Z",
                    timeMax=end_time.isoformat() + "Z",
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            self.logger.info(f"🔍 Events result: {events_result}")

            events = events_result.get("items", [])
            event_list = []

            for event in events:
                self.logger.info(f"🔍 Event: {event}")
                calendar_event = self._parse_calendar_event(event)
                if calendar_event:
                    event_list.append(calendar_event)

            self.logger.info(f"🔍 Event list: {event_list}")

            self.logger.info(f"✅ Retrieved {len(event_list)} events")
            return event_list

        except Exception as e:
            self.logger.error(f"❌ Failed to list events: {e}")
            return []

    async def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Create a new calendar event."""
        if not self.is_authenticated():
            self.logger.error("❌ Calendar service not authenticated")
            return None

        try:
            self.logger.info(f"📅 Creating event: {title}")

            # Parse times
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))

            # Create event object
            event = {
                "summary": title,
                "start": {
                    "dateTime": start_dt.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_dt.isoformat(),
                    "timeZone": "UTC",
                },
            }

            if description:
                event["description"] = description

            if location:
                event["location"] = location

            if attendees:
                event["attendees"] = [
                    {"email": email} for email in attendees if isinstance(email, str)
                ]

            if not self.service:
                raise RuntimeError("Calendar service not authenticated")

            # Create event
            created_event = (
                self.service.events().insert(calendarId="primary", body=event).execute()
            )

            event_id = created_event.get("id")
            self.logger.info(f"✅ Event created successfully: {event_id}")
            return event_id

        except Exception as e:
            self.logger.error(f"❌ Failed to create event: {e}")
            return None

    def _parse_calendar_event(self, event: Dict[str, Any]) -> Optional[CalendarEvent]:
        """Parse Google Calendar event into CalendarEvent model."""
        try:
            # Get start and end times
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))

            # Parse datetime
            if "T" in start:  # datetime
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
            else:  # date only
                start_dt = datetime.fromisoformat(start + "T00:00:00+00:00")
                end_dt = datetime.fromisoformat(end + "T23:59:59+00:00")

            # Get attendees
            attendees = []
            if "attendees" in event:
                attendees = [
                    attendee.get("email", "") for attendee in event["attendees"]
                ]

            return CalendarEvent(
                id=event["id"],
                title=event.get("summary", ""),
                description=event.get("description", ""),
                start_time=start_dt,
                end_time=end_dt,
                location=event.get("location", ""),
                attendees=attendees,
                reminders=[],  # Would need to parse reminders if needed
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to parse calendar event: {e}")
            return None
