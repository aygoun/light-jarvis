"""MCP server implementation for Jarvis."""

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
import sys
import os
import json

from jarvis_shared.logger import get_logger
from jarvis_shared.config import MCPConfig, JarvisConfig
from jarvis_shared.google_auth import GoogleAuthManager


class ToolCall(BaseModel):
    """Tool call request model."""

    id: str
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    """Tool execution result model."""

    tool_call_id: str
    content: str
    success: bool
    error: Optional[str] = None


class MCPServer:
    """MCP server for managing and executing tools."""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.logger = get_logger("jarvis.mcp.server")
        self.app = FastAPI(title="Jarvis MCP Server", version="0.1.0")
        self.tools_registry: Dict[str, Any] = {}
        self.oauth_results: Dict[str, Any] = {}  # Store OAuth results
        self.oauth_event: Optional[asyncio.Event] = None

        # Full Jarvis config for authentication
        self.jarvis_config: Optional[JarvisConfig] = None
        self.google_auth: Optional[GoogleAuthManager] = None
        self.gmail_client: Optional[Any] = None
        self.calendar_client: Optional[Any] = None
        self.auth_initialized = False

        # Tool instances
        self.gmail_tool: Optional[Any] = None
        self.calendar_tool: Optional[Any] = None
        self.notification_tool: Optional[Any] = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes for MCP server."""

        @self.app.get("/tools")
        async def list_tools():
            """List all available tools."""
            return {"tools": list(self.tools_registry.values())}

        @self.app.post("/tools/execute")
        async def execute_tool(tool_call: ToolCall) -> ToolResult:
            """Execute a tool call."""
            try:
                if tool_call.name not in self.tools_registry:
                    raise HTTPException(
                        status_code=404, detail=f"Tool '{tool_call.name}' not found"
                    )

                # Execute real tool or simulate if not available
                result = await self._execute_tool(tool_call.name, tool_call.arguments)

                return ToolResult(
                    tool_call_id=tool_call.id, content=str(result), success=True
                )

            except Exception as e:
                self.logger.error(f"Tool execution failed: {e}")
                return ToolResult(
                    tool_call_id=tool_call.id, content="", success=False, error=str(e)
                )

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            google_authenticated = (
                self.google_auth.is_authenticated() if self.google_auth else False
            )
            return {
                "status": "healthy",
                "tools_count": len(self.tools_registry),
                "auth_initialized": self.auth_initialized,
                "google_authenticated": google_authenticated,
            }

        @self.app.post("/auth/init")
        async def initialize_auth():
            """Initialize authentication components."""
            try:
                await self._initialize_auth()
                return {"status": "success", "message": "Authentication initialized"}
            except Exception as e:
                self.logger.error(f"❌ Auth initialization failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/auth/google")
        async def authenticate_google():
            """Authenticate with Google services (Gmail + Calendar)."""
            try:
                if not self.auth_initialized:
                    await self._initialize_auth()

                if self.google_auth:
                    success = await self.google_auth.authenticate()
                    if success:
                        # Update clients with authenticated services
                        await self._update_clients_with_auth()
                    return {
                        "status": "success" if success else "failed",
                        "services": ["gmail", "calendar"],
                        "authenticated": self.google_auth.is_authenticated(),
                    }
                else:
                    raise HTTPException(
                        status_code=500, detail="Google auth manager not initialized"
                    )
            except Exception as e:
                self.logger.error(f"❌ Google authentication failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/auth/gmail")
        async def authenticate_gmail():
            """Authenticate with Gmail (uses unified Google auth)."""
            return await authenticate_google()

        @self.app.post("/auth/calendar")
        async def authenticate_calendar():
            """Authenticate with Calendar (uses unified Google auth)."""
            return await authenticate_google()

        @self.app.get("/auth/status")
        async def auth_status():
            """Get authentication status for all services."""
            google_status = (
                self.google_auth.get_auth_status()
                if self.google_auth
                else {
                    "authenticated": False,
                    "has_credentials": False,
                    "credentials_valid": False,
                    "gmail_service_available": False,
                    "calendar_service_available": False,
                    "credentials_file_exists": False,
                    "token_file_exists": False,
                    "scopes": [],
                }
            )

            return {
                "auth_initialized": self.auth_initialized,
                "google": google_status,
                "gmail": {
                    "client_available": self.gmail_client is not None,
                    "authenticated": google_status["authenticated"],
                    "service_available": google_status["gmail_service_available"],
                },
                "calendar": {
                    "client_available": self.calendar_client is not None,
                    "authenticated": google_status["authenticated"],
                    "service_available": google_status["calendar_service_available"],
                },
                "oauth_callback_url": (
                    self.jarvis_config.google.oauth_callback_url
                    if self.jarvis_config
                    else None
                ),
            }

        @self.app.get("/oauth2/callback")
        async def oauth_callback(request: Request):
            """Handle OAuth2 callback from Google."""
            try:
                # Get the authorization code from query parameters
                code = request.query_params.get("code")
                error = request.query_params.get("error")
                state = request.query_params.get("state")

                if error:
                    self.logger.error(f"❌ OAuth error: {error}")
                    self.oauth_results["error"] = error
                elif code:
                    self.logger.info("✅ OAuth authorization code received")
                    self.oauth_results["code"] = code
                    self.oauth_results["state"] = state
                else:
                    self.logger.error("❌ No authorization code or error received")
                    self.oauth_results["error"] = "No authorization code received"

                # Signal that we received the callback
                if self.oauth_event:
                    self.oauth_event.set()

                # Return a simple success page
                css_class = "success" if code else "error"
                title = "✅ Success!" if code else "❌ Error"
                message = (
                    "Authentication successful! Jarvis has been granted access to your Google account."
                    if code
                    else f"Authentication failed: {error or 'Unknown error'}"
                )

                html_content = f"""
                <html>
                    <head>
                        <title>Jarvis OAuth Success</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
                            .success {{ color: green; }}
                            .error {{ color: red; }}
                        </style>
                    </head>
                    <body>
                        <h1>Jarvis Authentication</h1>
                        <div class="{css_class}">
                            <h2>{title}</h2>
                            <p>{message}</p>
                        </div>
                        <p>You can close this window now.</p>
                    </body>
                </html>
                """

                return HTMLResponse(html_content)

            except Exception as e:
                self.logger.error(f"❌ OAuth callback error: {e}")
                self.oauth_results["error"] = str(e)
                if self.oauth_event:
                    self.oauth_event.set()
                return HTMLResponse(
                    f"<html><body><h1>Error</h1><p>{e}</p></body></html>",
                    status_code=500,
                )

    def register_tool(self, tool_config: Dict[str, Any]):
        """Register a tool with the server."""
        tool_name = tool_config["name"]
        self.tools_registry[tool_name] = tool_config
        self.logger.info(f"🔧 Registered tool: {tool_name}")

    async def wait_for_oauth_callback(self, timeout: int = 300) -> Dict[str, Any]:
        """Wait for OAuth2 callback and return the result."""
        self.oauth_event = asyncio.Event()
        self.oauth_results.clear()

        try:
            # Wait for the callback with timeout
            await asyncio.wait_for(self.oauth_event.wait(), timeout=timeout)
            return self.oauth_results.copy()
        except asyncio.TimeoutError:
            self.logger.error("❌ OAuth callback timeout")
            return {"error": "OAuth callback timeout"}
        finally:
            self.oauth_event = None
            self.oauth_results.clear()

    async def _initialize_auth(self):
        """Initialize authentication components."""
        try:
            self.logger.info("🔐 Initializing unified Google authentication...")

            # Load full Jarvis config
            self.jarvis_config = JarvisConfig()

            # Initialize unified Google auth manager with MCP server reference
            self.google_auth = GoogleAuthManager(
                self.jarvis_config.google, mcp_server=self
            )
            self.logger.info("✅ Google auth manager initialized")

            # Add paths for Google client imports
            # Get the workspace root (jarvis directory)
            current_file = os.path.abspath(__file__)
            # Go up: server.py -> jarvis_mcp -> mcp-server -> packages -> jarvis
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            )

            gmail_path = os.path.join(project_root, "packages", "tools", "gmail-tool")
            calendar_path = os.path.join(
                project_root, "packages", "tools", "calendar-tool"
            )

            self.logger.debug(f"🔍 Project root: {project_root}")
            self.logger.debug(f"🔍 Gmail path: {gmail_path}")
            self.logger.debug(f"🔍 Calendar path: {calendar_path}")

            if gmail_path not in sys.path:
                sys.path.insert(0, gmail_path)
            if calendar_path not in sys.path:
                sys.path.insert(0, calendar_path)

            # Import and initialize Gmail client
            try:
                from jarvis_gmail.gmail_client import GmailClient

                self.gmail_client = GmailClient(self.jarvis_config.google)
                self.logger.info("✅ Gmail client wrapper initialized")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize Gmail client: {e}")
                self.gmail_client = None

            # Import and initialize Calendar client
            try:
                from jarvis_calendar.calendar_client import CalendarClient

                self.calendar_client = CalendarClient(self.jarvis_config.google)
                self.logger.info("✅ Calendar client wrapper initialized")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize Calendar client: {e}")
                self.calendar_client = None

            self.auth_initialized = True
            self.logger.info("🎉 Authentication initialization complete!")

            # Check credentials file and auto-authenticate
            if self.jarvis_config.google.credentials_file:
                if os.path.exists(self.jarvis_config.google.credentials_file):
                    self.logger.info(
                        f"✅ Google credentials file found: {self.jarvis_config.google.credentials_file}"
                    )

                    # Auto-authenticate on startup
                    self.logger.info("🚀 Starting automatic Google authentication...")
                    success = await self.google_auth.authenticate()
                    if success:
                        self.logger.info("🎉 Automatic authentication successful!")
                        await self._update_clients_with_auth()
                    else:
                        self.logger.warning(
                            "⚠️  Automatic authentication failed - manual auth required"
                        )
                else:
                    self.logger.warning(
                        f"⚠️  Google credentials file not found: {self.jarvis_config.google.credentials_file}"
                    )
                    self.logger.info(
                        "   Download credentials from Google Cloud Console to enable authentication"
                    )

        except Exception as e:
            self.logger.error(f"❌ Authentication initialization failed: {e}")
            raise

    async def _update_clients_with_auth(self):
        """Update client services with authenticated Google services."""
        if not self.google_auth or not self.google_auth.is_authenticated():
            return

        try:
            gmail_service = self.google_auth.get_gmail_service()
            calendar_service = self.google_auth.get_calendar_service()

            if self.gmail_client and gmail_service:
                self.gmail_client.service = gmail_service
                self.logger.debug("✅ Gmail client updated with authenticated service")

            if self.calendar_client and calendar_service:
                self.calendar_client.service = calendar_service
                self.logger.debug(
                    "✅ Calendar client updated with authenticated service"
                )

        except Exception as e:
            self.logger.error(f"❌ Failed to update clients with auth: {e}")

    async def _execute_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool using the appropriate tool class."""

        try:
            # Route to appropriate tool class
            if tool_name.startswith("gmail_"):
                if self.gmail_tool:
                    return await self.gmail_tool.execute(tool_name, arguments)
                else:
                    return {"status": "error", "message": "Gmail tool not initialized"}

            elif tool_name.startswith("calendar_"):
                if self.calendar_tool:
                    return await self.calendar_tool.execute(tool_name, arguments)
                else:
                    return {
                        "status": "error",
                        "message": "Calendar tool not initialized",
                    }

            elif tool_name in [
                "send_notification",
                "schedule_reminder",
                "cancel_reminder",
                "list_reminders",
            ]:
                if self.notification_tool:
                    return await self.notification_tool.execute(tool_name, arguments)
                else:
                    return {
                        "status": "error",
                        "message": "Notification tool not initialized",
                    }

            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        except Exception as e:
            self.logger.error(f"❌ Tool execution failed for {tool_name}: {e}")
            return {"status": "error", "message": str(e)}

    async def start_server(self):
        """Start the MCP server."""
        import uvicorn
        import asyncio

        self.logger.info(
            f"🚀 Starting MCP server on {self.config.host}:{self.config.port}"
        )

        # Register default tools
        self._register_default_tools()

        # Start HTTP server first
        config = uvicorn.Config(
            self.app, host=self.config.host, port=self.config.port, log_level="info"
        )
        server = uvicorn.Server(config)

        # Start server in background task
        server_task = asyncio.create_task(server.serve())

        # Give server a moment to start
        await asyncio.sleep(1)

        # Now initialize authentication (server is running for OAuth callbacks)
        try:
            await self._initialize_auth()
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize authentication: {e}")
            self.logger.info("🔄 Server will continue without authentication")

        # Wait for server to finish
        await server_task

    def _register_default_tools(self):
        """Register default tools with the server by loading from each tool class."""
        try:
            # Add tool packages to path
            import sys
            import os

            current_file = os.path.abspath(__file__)
            # Go up: server.py -> jarvis_mcp -> mcp-server -> packages -> jarvis
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            )

            gmail_path = os.path.join(project_root, "packages", "tools", "gmail-tool")
            calendar_path = os.path.join(
                project_root, "packages", "tools", "calendar-tool"
            )
            notification_path = os.path.join(
                project_root, "packages", "tools", "notification-tool"
            )

            if gmail_path not in sys.path:
                sys.path.insert(0, gmail_path)
            if calendar_path not in sys.path:
                sys.path.insert(0, calendar_path)
            if notification_path not in sys.path:
                sys.path.insert(0, notification_path)

            # Import tool classes
            from jarvis_gmail.gmail_tool import GmailTool
            from jarvis_calendar.calendar_tool import CalendarTool
            from jarvis_notification.notification_tool import NotificationTool

            # Initialize tool instances
            self.gmail_tool = (
                GmailTool(self.jarvis_config.google) if self.jarvis_config else None
            )
            self.calendar_tool = (
                CalendarTool(self.jarvis_config.google) if self.jarvis_config else None
            )
            self.notification_tool = NotificationTool()

            # Register tools from each tool class
            if self.gmail_tool:
                for tool_def in self.gmail_tool.get_tool_definitions():
                    self.register_tool(tool_def)
                    self.logger.info(f"🔧 Registered Gmail tool: {tool_def['name']}")
            else:
                # Register Gmail tools even without config (for tool definitions)
                temp_gmail_tool = GmailTool(None)
                for tool_def in temp_gmail_tool.get_tool_definitions():
                    self.register_tool(tool_def)
                    self.logger.info(f"🔧 Registered Gmail tool: {tool_def['name']}")

            if self.calendar_tool:
                for tool_def in self.calendar_tool.get_tool_definitions():
                    self.register_tool(tool_def)
                    self.logger.info(f"🔧 Registered Calendar tool: {tool_def['name']}")
            else:
                # Register Calendar tools even without config (for tool definitions)
                temp_calendar_tool = CalendarTool(None)
                for tool_def in temp_calendar_tool.get_tool_definitions():
                    self.register_tool(tool_def)
                    self.logger.info(f"🔧 Registered Calendar tool: {tool_def['name']}")

            for tool_def in self.notification_tool.get_tool_definitions():
                self.register_tool(tool_def)
                self.logger.info(f"🔧 Registered Notification tool: {tool_def['name']}")

        except Exception as e:
            self.logger.error(f"❌ Failed to register tools: {e}")
            raise Exception(f"Failed to register tools: {e}")
