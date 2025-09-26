"""Gmail API client for email operations."""

import base64
import email
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from jarvis_shared.models import EmailMessage
from jarvis_shared.logger import get_logger
from jarvis_shared.config import GoogleConfig


class GmailClient:
    """Client for Gmail API operations."""

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
    ]

    def __init__(self, config: GoogleConfig):
        self.config = config
        self.logger = get_logger("jarvis.gmail.client")
        self.service = None
        self.credentials = None

    async def authenticate(self) -> bool:
        """Authenticate with Google Gmail API."""
        try:
            creds = None

            # Load existing token
            if self.config.token_file and os.path.exists(self.config.token_file):
                creds = Credentials.from_authorized_user_file(
                    self.config.token_file, self.SCOPES
                )

            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.config.credentials_file or not os.path.exists(
                        self.config.credentials_file
                    ):
                        self.logger.error("❌ Google credentials file not found")
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config.credentials_file, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials
                if self.config.token_file:
                    with open(self.config.token_file, "w") as token:
                        token.write(creds.to_json())

            self.credentials = creds
            self.service = build("gmail", "v1", credentials=creds)
            self.logger.info("✅ Gmail authentication successful")
            return True

        except Exception as e:
            self.logger.error(f"❌ Gmail authentication failed: {e}")
            return False

    async def read_emails(
        self, query: str = "", max_results: int = 10
    ) -> List[EmailMessage]:
        """Read emails from Gmail."""
        if not self.service:
            if not await self.authenticate():
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
        if not self.service:
            if not await self.authenticate():
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
