#!/usr/bin/env python3
"""
Jarvis CLI - Simple command-line interface to get latest Revolut email and next calendar event.
"""

import asyncio
import json
import ast
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import argparse
import requests
from pathlib import Path

# Add the packages to the Python path
sys.path.append(str(Path(__file__).parent.parent / "packages" / "shared"))

from jarvis_shared.logger import get_logger


class JarvisCLI:
    """Simple CLI for Jarvis MCP server operations."""

    def __init__(self, mcp_server_url: str = "http://localhost:3000"):
        self.mcp_server_url = mcp_server_url
        self.logger = get_logger("jarvis.cli")

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        try:
            # Generate a unique tool call ID
            tool_call_id = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            payload = {"id": tool_call_id, "name": tool_name, "arguments": arguments}

            self.logger.debug(f"Calling tool {tool_name} with arguments: {arguments}")

            response = requests.post(
                f"{self.mcp_server_url}/tools/execute", json=payload, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"Tool call successful: {result}")
                return result
            else:
                self.logger.error(
                    f"Tool call failed with status {response.status_code}: {response.text}"
                )
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except requests.exceptions.ConnectionError:
            self.logger.error("❌ Could not connect to MCP server. Is it running?")
            return {"success": False, "error": "Could not connect to MCP server"}
        except Exception as e:
            self.logger.error(f"❌ Tool call failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_latest_revolut_email(self) -> Optional[Dict[str, Any]]:
        """Get the latest email from Revolut."""
        print("📧 Searching for latest Revolut email...")

        # Search for emails from Revolut
        result = await self.call_tool(
            "gmail_read_emails",
            {"query": "from:revolut.com OR from:noreply@revolut.com", "max_results": 1},
        )

        if result.get("success"):
            # The content field contains a string representation of the data structure
            content = result.get("content")

            # Parse the content as a Python dictionary string
            try:
                if isinstance(content, str):
                    emails_data = ast.literal_eval(content)
                else:
                    emails_data = content

                # Handle the response format - content is a dict with emails key
                if isinstance(emails_data, dict) and "emails" in emails_data:
                    emails = emails_data["emails"]
                else:
                    print(f"⚠️  Unexpected email data format: {emails_data}")
                    return None
            except (ValueError, SyntaxError) as e:
                print(f"⚠️  Could not parse email data: {e}")
                return None

            if emails and len(emails) > 0:
                latest_email = emails[0]
                # Map the response fields to expected format
                email_data = {
                    "subject": latest_email.get("subject", "No Subject"),
                    "from": latest_email.get(
                        "sender", latest_email.get("from", "Unknown Sender")
                    ),
                    "date": latest_email.get(
                        "timestamp", latest_email.get("date", "Unknown Date")
                    ),
                    "snippet": latest_email.get(
                        "body", latest_email.get("snippet", "No preview available")
                    ),
                }
                print(f"✅ Found latest Revolut email from {email_data['from']}")
                return email_data
            else:
                print("ℹ️  No Revolut emails found")
                return None
        else:
            print(
                f"❌ Failed to get Revolut emails: {result.get('error', 'Unknown error')}"
            )
            return None

    async def get_next_calendar_event(self) -> Optional[Dict[str, Any]]:
        """Get the next upcoming calendar event."""
        print("📅 Looking for next calendar event...")

        # Get events starting from now
        today = datetime.now().strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        result = await self.call_tool(
            "calendar_list_events",
            {"start_date": today, "end_date": next_week, "max_results": 1},
        )

        if result.get("success"):
            # The content field contains a string representation of the data structure
            content = result.get("content")

            # Parse the content as a Python dictionary string
            try:
                if isinstance(content, str):
                    events_data = ast.literal_eval(content)
                else:
                    events_data = content

                # Handle the response format - content is a dict with events key
                if isinstance(events_data, dict) and "events" in events_data:
                    events = events_data["events"]
                else:
                    print(f"⚠️  Unexpected calendar data format: {events_data}")
                    return None
            except (ValueError, SyntaxError) as e:
                print(f"⚠️  Could not parse calendar data: {e}")
                return None

            if events and len(events) > 0:
                next_event = events[0]
                # Map the response fields to expected format
                event_data = {
                    "title": next_event.get("title", "Untitled Event"),
                    "start_time": next_event.get("start_time", "Unknown Time"),
                    "end_time": next_event.get("end_time", "Unknown Time"),
                    "location": next_event.get("location", "No location"),
                    "description": next_event.get("description", "No description"),
                }
                print(f"✅ Found next event: {event_data['title']}")
                return event_data
            else:
                print("ℹ️  No upcoming events found in the next 7 days")
                return None
        else:
            print(
                f"❌ Failed to get calendar events: {result.get('error', 'Unknown error')}"
            )
            return None

    def format_email(self, email: Dict[str, Any]) -> str:
        """Format email for display."""
        if not email:
            return "No email data"

        subject = email.get("subject", "No Subject")
        sender = email.get("from", "Unknown Sender")
        date = email.get("date", "Unknown Date")
        snippet = email.get("snippet", "No preview available")

        return f"""
📧 Latest Revolut Email:
   From: {sender}
   Subject: {subject}
   Date: {date}
   Preview: {snippet}
"""

    def format_event(self, event: Dict[str, Any]) -> str:
        """Format calendar event for display."""
        if not event:
            return "No event data"

        title = event.get("title", "Untitled Event")
        start_time = event.get("start_time", "Unknown Time")
        end_time = event.get("end_time", "Unknown Time")
        location = event.get("location", "No location")
        description = event.get("description", "No description")

        return f"""
📅 Next Calendar Event:
   Title: {title}
   Time: {start_time} - {end_time}
   Location: {location}
   Description: {description}
"""

    async def run(self, show_email: bool = True, show_calendar: bool = True):
        """Run the CLI with specified options."""
        print("🤖 Jarvis CLI - Getting your latest info...")
        print("=" * 50)

        results = {}

        if show_email:
            email = await self.get_latest_revolut_email()
            results["email"] = email

        if show_calendar:
            event = await self.get_next_calendar_event()
            results["event"] = event

        print("\n" + "=" * 50)
        print("📋 SUMMARY")
        print("=" * 50)

        if show_email:
            print(self.format_email(results.get("email")))

        if show_calendar:
            print(self.format_event(results.get("event")))

        return results


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Jarvis CLI - Get latest Revolut email and next calendar event"
    )
    parser.add_argument(
        "--server", default="http://localhost:3000", help="MCP server URL"
    )
    parser.add_argument("--no-email", action="store_true", help="Skip email lookup")
    parser.add_argument(
        "--no-calendar", action="store_true", help="Skip calendar lookup"
    )
    parser.add_argument("--email-only", action="store_true", help="Only show email")
    parser.add_argument(
        "--calendar-only", action="store_true", help="Only show calendar"
    )

    args = parser.parse_args()

    # Determine what to show
    show_email = not args.no_email and not args.calendar_only
    show_calendar = not args.no_calendar and not args.email_only

    if not show_email and not show_calendar:
        print("❌ Nothing to show. Use --help for options.")
        return

    cli = JarvisCLI(args.server)
    await cli.run(show_email=show_email, show_calendar=show_calendar)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
