"""Gmail API client for email operations."""

import base64
import email
from datetime import datetime
from typing import List, Optional, Dict, Any

from jarvis_shared.models import EmailMessage
from jarvis_shared.logger import get_logger
from jarvis_shared.config import GoogleConfig


class GmailClient:
    """Client for Gmail API operations."""

    def __init__(self, config: GoogleConfig):
        self.config = config
        self.logger = get_logger("jarvis.gmail.client")
        self.service = None
        self.credentials = None

    def is_authenticated(self) -> bool:
        """Check if the Gmail service is authenticated and ready to use."""
        return self.service is not None

    def set_service(self, service, credentials=None):
        """Set the authenticated Gmail service."""
        self.service = service
        if credentials:
            self.credentials = credentials
        self.logger.info("✅ Gmail service authenticated and ready")

    async def read_emails(
        self, query: str = "", max_results: int = 10
    ) -> List[EmailMessage]:
        """Read emails from Gmail."""
        if not self.is_authenticated():
            self.logger.error("❌ Gmail service not authenticated")
            self.logger.info(
                "   Ensure GoogleAuthManager has authenticated the service"
            )
            return []

        try:
            if not self.service:
                raise RuntimeError("Gmail service not authenticated")

            self.logger.info(f"📧 Reading emails with query: '{query}'")

            # Search for messages
            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            email_list = []

            for message in messages:
                # Get full message details
                if not self.service:
                    continue
                msg = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=message["id"])
                    .execute()
                )

                email_msg = self._parse_email_message(msg)
                if email_msg:
                    email_list.append(email_msg)

            self.logger.info(f"✅ Retrieved {len(email_list)} emails")
            return email_list

        except Exception as e:
            self.logger.error(f"❌ Failed to read emails: {e}")
            return []

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email via Gmail."""
        return False  # Disable email sending for now

        if not self.is_authenticated():
            self.logger.error("❌ Gmail service not authenticated")
            return False

        try:
            self.logger.info(f"📤 Sending email to {to}")

            # Create message
            message = self._create_message(to, subject, body)

            # Send message
            result = (
                self.service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )

            self.logger.info(f"✅ Email sent successfully: {result.get('id')}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to send email: {e}")
            return False

    def _parse_email_message(self, msg: Dict[str, Any]) -> Optional[EmailMessage]:
        """Parse Gmail API message into EmailMessage model."""
        try:
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}

            # Get email body
            body = self._extract_body(msg["payload"])

            # Parse timestamp
            timestamp = datetime.fromtimestamp(int(msg["internalDate"]) / 1000)

            return EmailMessage(
                id=msg["id"],
                subject=headers.get("Subject", ""),
                sender=headers.get("From", ""),
                recipients=[headers.get("To", "")],
                body=body,
                timestamp=timestamp,
                is_read="UNREAD" not in msg.get("labelIds", []),
                labels=msg.get("labelIds", []),
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to parse email message: {e}")
            return None

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract body text from email payload."""
        body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode("utf-8")
                        break
        elif payload["mimeType"] == "text/plain":
            data = payload["body"].get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8")

        return body

    def _create_message(self, to: str, subject: str, body: str) -> Dict[str, str]:
        """Create email message for sending."""
        message = email.message.EmailMessage()
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {"raw": raw_message}
