"""Unified Google authentication manager for Gmail and Calendar."""

import os
import asyncio
from typing import Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .logger import get_logger
from .config import GoogleConfig


class GoogleAuthManager:
    """Unified authentication manager for all Google services."""

    def __init__(self, config: GoogleConfig, mcp_server=None):
        self.config = config
        self.logger = get_logger("jarvis.google.auth")
        self.credentials: Optional[Credentials] = None
        self.gmail_service = None
        self.calendar_service = None
        self._auth_lock = asyncio.Lock()
        self.mcp_server = mcp_server  # Reference to MCP server for OAuth coordination

    async def authenticate(self, force_reauth: bool = False) -> bool:
        """Authenticate with Google services using unified OAuth2 flow."""
        async with self._auth_lock:
            try:
                self.logger.info("🔐 Starting Google authentication...")

                # Try to load existing credentials
                if not force_reauth:
                    creds = self._load_existing_credentials()
                    if creds and creds.valid:
                        self.credentials = creds
                        self.logger.info("✅ Using existing valid credentials")
                        return await self._build_services()

                # Refresh expired credentials if possible
                if not force_reauth and creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        self.credentials = creds
                        self._save_credentials(creds)
                        self.logger.info("✅ Refreshed expired credentials")
                        return await self._build_services()
                    except Exception as e:
                        self.logger.warning(f"⚠️  Failed to refresh credentials: {e}")

                # Perform new OAuth2 flow
                return await self._perform_oauth_flow()

            except Exception as e:
                self.logger.error(f"❌ Google authentication failed: {e}")
                return False

    def _load_existing_credentials(self) -> Optional[Credentials]:
        """Load existing credentials from token file."""
        if not self.config.token_file or not os.path.exists(self.config.token_file):
            return None

        try:
            creds = Credentials.from_authorized_user_file(
                self.config.token_file, self.config.scopes
            )
            self.logger.debug("📄 Loaded existing credentials from file")
            return creds
        except Exception as e:
            self.logger.warning(f"⚠️  Failed to load existing credentials: {e}")
            return None

    async def _perform_oauth_flow(self) -> bool:
        """Perform OAuth2 flow to get new credentials."""
        if not self.config.credentials_file or not os.path.exists(
            self.config.credentials_file
        ):
            self.logger.error("❌ Google credentials file not found")
            self.logger.info(f"   Expected location: {self.config.credentials_file}")
            self.logger.info(
                "   Download from Google Cloud Console > APIs & Services > Credentials"
            )
            return False

        try:
            self.logger.info("🌐 Starting OAuth2 flow...")
            self.logger.info(
                f"   Callback URL will be: {self.config.oauth_callback_url}"
            )

            flow = InstalledAppFlow.from_client_secrets_file(
                self.config.credentials_file, self.config.scopes
            )

            # Set the redirect URI to match our MCP server callback
            flow.redirect_uri = self.config.oauth_callback_url

            # Get the authorization URL
            auth_url, state = flow.authorization_url(
                access_type="offline", include_granted_scopes="true"
            )

            self.logger.info(
                f"🌐 Please visit this URL to authorize the application: {auth_url}"
            )
            self.logger.info(
                f"🔄 Waiting for OAuth callback at {self.config.oauth_callback_url}"
            )

            # Open browser automatically
            import webbrowser

            webbrowser.open(auth_url)

            # If we have an MCP server, coordinate with it for OAuth callback
            if self.mcp_server:
                self.logger.info("🔄 Using MCP server for OAuth callback coordination")
                # Wait for the callback through the MCP server
                result = await self.mcp_server.wait_for_oauth_callback(timeout=300)
                if "code" in result:
                    # Exchange the authorization code for credentials
                    flow.fetch_token(code=result["code"])
                    creds = flow.credentials
                else:
                    raise Exception(
                        f"OAuth callback failed: {result.get('error', 'Unknown error')}"
                    )
            else:
                # Fallback: use run_local_server on a different port
                temp_port = 3001
                self.logger.info(f"🔄 Using temporary OAuth server on port {temp_port}")
                creds = flow.run_local_server(
                    host=self.config.oauth_callback_host,
                    port=temp_port,
                    open_browser=False,  # We already opened the browser
                )

            self.credentials = creds
            self._save_credentials(creds)

            self.logger.info("✅ OAuth2 flow completed successfully")
            return await self._build_services()

        except Exception as e:
            self.logger.error(f"❌ OAuth2 flow failed: {e}")
            return False

    def _save_credentials(self, creds: Credentials):
        """Save credentials to token file."""
        if not self.config.token_file:
            return

        try:
            # Ensure directory exists
            token_dir = Path(self.config.token_file).parent
            token_dir.mkdir(parents=True, exist_ok=True)

            with open(self.config.token_file, "w") as token:
                token.write(creds.to_json())

            self.logger.debug(f"💾 Saved credentials to {self.config.token_file}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save credentials: {e}")

    async def _build_services(self) -> bool:
        """Build Gmail and Calendar service objects."""
        if not self.credentials:
            return False

        try:
            # Build Gmail service
            self.gmail_service = build("gmail", "v1", credentials=self.credentials)
            self.logger.info("✅ Gmail service initialized")

            # Build Calendar service
            self.calendar_service = build(
                "calendar", "v3", credentials=self.credentials
            )
            self.logger.info("✅ Calendar service initialized")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to build Google services: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if currently authenticated with valid services."""
        return (
            self.credentials is not None
            and self.credentials.valid
            and self.gmail_service is not None
            and self.calendar_service is not None
        )

    def get_gmail_service(self):
        """Get Gmail service object."""
        return self.gmail_service

    def get_calendar_service(self):
        """Get Calendar service object."""
        return self.calendar_service

    async def revoke_authentication(self) -> bool:
        """Revoke authentication and clear credentials."""
        try:
            if self.credentials:
                # Revoke the credentials
                self.credentials.revoke(Request())

            # Clear services
            self.gmail_service = None
            self.calendar_service = None
            self.credentials = None

            # Remove token file
            if self.config.token_file and os.path.exists(self.config.token_file):
                os.remove(self.config.token_file)

            self.logger.info("✅ Authentication revoked successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to revoke authentication: {e}")
            return False

    def get_auth_status(self) -> dict:
        """Get detailed authentication status."""
        return {
            "authenticated": self.is_authenticated(),
            "has_credentials": self.credentials is not None,
            "credentials_valid": self.credentials.valid if self.credentials else False,
            "gmail_service_available": self.gmail_service is not None,
            "calendar_service_available": self.calendar_service is not None,
            "credentials_file_exists": (
                self.config.credentials_file
                and os.path.exists(self.config.credentials_file)
            ),
            "token_file_exists": (
                self.config.token_file and os.path.exists(self.config.token_file)
            ),
            "scopes": self.config.scopes,
        }
