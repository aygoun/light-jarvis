"""Gmail tool implementation for MCP integration."""

import json
from typing import Dict, Any, List

from jarvis_shared.logger import get_logger
from jarvis_shared.config import GoogleConfig
from .gmail_client import GmailClient


class GmailTool:
    """Gmail tool for MCP integration."""

    def __init__(self, config: GoogleConfig):
        self.config = config
        self.logger = get_logger("jarvis.gmail.tool")
        self.client = GmailClient(config)

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Gmail tool operation."""

        try:
            if tool_name == "gmail_read_emails":
                return await self._read_emails(arguments)
            elif tool_name == "gmail_send_email":
                return await self._send_email(arguments)
            else:
                raise ValueError(f"Unknown Gmail tool: {tool_name}")

        except Exception as e:
            self.logger.error(f"❌ Gmail tool execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _read_emails(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Read emails from Gmail."""
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)

        emails = await self.client.read_emails(query, max_results)

        # Convert to serializable format
        email_data = []
        for email in emails:
            email_data.append(
                {
                    "id": email.id,
                    "subject": email.subject,
                    "sender": email.sender,
                    "recipients": email.recipients,
                    "body": (
                        email.body[:500] + "..."
                        if len(email.body) > 500
                        else email.body
                    ),  # Truncate long bodies
                    "timestamp": email.timestamp.isoformat(),
                    "is_read": email.is_read,
                    "labels": email.labels,
                }
            )

        return {"success": True, "emails": email_data, "total": len(email_data)}

    async def _send_email(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Gmail."""
        to = arguments.get("to")
        subject = arguments.get("subject")
        body = arguments.get("body")

        if not all([to, subject, body]):
            return {
                "success": False,
                "error": "Missing required fields: to, subject, body",
            }

        success = await self.client.send_email(to, subject, body)

        if success:
            return {
                "success": True,
                "message": f"Email sent to {to}",
                "timestamp": "2024-01-15T11:00:00Z",  # Would be actual timestamp
            }
        else:
            return {"success": False, "error": "Failed to send email"}

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for MCP registration."""
        return [
            {
                "name": "gmail_read_emails",
                "description": "Read emails from Gmail",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for emails (e.g., 'from:john@example.com', 'is:unread')",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of emails to return",
                            "default": 10,
                        },
                    },
                },
            },
            {
                "name": "gmail_send_email",
                "description": "Send an email via Gmail",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address",
                        },
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body content"},
                    },
                    "required": ["to", "subject", "body"],
                },
            },
        ]
