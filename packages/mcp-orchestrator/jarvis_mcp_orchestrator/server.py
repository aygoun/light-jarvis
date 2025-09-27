"""MCP Orchestrator Server - consolidates all MCP tools."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis_shared.config import JarvisConfig, MCPConfig
from jarvis_shared.logger import get_logger
from jarvis_shared.google_auth import GoogleAuthManager

from .tools.gmail_tool import GmailTool
from .tools.calendar_tool import CalendarTool
from .tools.notification_tool import NotificationTool
from .tools.hue_tool import HueTool


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


class MCPOrchestratorServer:
    """MCP Orchestrator Server that consolidates all MCP tools."""

    def __init__(self, config: MCPConfig):
        self.config = config
        self.logger = get_logger("jarvis.mcp.orchestrator")
        self.app = FastAPI(
            title="Jarvis MCP Orchestrator",
            version="0.1.0",
            description="Consolidates all MCP tools (Gmail, Calendar, Notification)",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Tool registry
        self.tools_registry: Dict[str, Any] = {}

        # Tool instances
        self.gmail_tool: Optional[GmailTool] = None
        self.calendar_tool: Optional[CalendarTool] = None
        self.notification_tool: Optional[NotificationTool] = None
        self.hue_tool: Optional[HueTool] = None

        # Authentication
        self.jarvis_config: Optional[JarvisConfig] = None
        self.google_auth: Optional[GoogleAuthManager] = None
        self.auth_initialized = False

        # OAuth callback coordination
        self.oauth_results: Dict[str, Any] = {}
        self.oauth_event: Optional[asyncio.Event] = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check() -> Dict[str, Any]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "mcp-orchestrator",
                "tools_count": len(self.tools_registry),
                "auth_initialized": self.auth_initialized,
                "google_authenticated": (
                    self.google_auth.is_authenticated() if self.google_auth else False
                ),
            }

        @self.app.get("/tools")
        async def list_tools() -> Dict[str, Any]:
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

                result = await self._execute_tool(tool_call.name, tool_call.arguments)

                return ToolResult(
                    tool_call_id=tool_call.id, content=str(result), success=True
                )

            except Exception as e:
                self.logger.error(f"Tool execution failed: {e}", exc_info=True)
                return ToolResult(
                    tool_call_id=tool_call.id, content="", success=False, error=str(e)
                )

        @self.app.post("/auth/init")
        async def initialize_auth() -> Dict[str, Any]:
            """Initialize authentication."""
            try:
                await self._initialize_auth()
                return {"status": "success", "message": "Authentication initialized"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/auth/google")
        async def authenticate_google() -> Dict[str, Any]:
            """Authenticate with Google services."""
            try:
                if not self.auth_initialized:
                    await self._initialize_auth()

                if self.google_auth:
                    success = await self.google_auth.authenticate()
                    if success:
                        await self._update_tools_with_auth()

                    return {
                        "status": "success" if success else "failed",
                        "authenticated": self.google_auth.is_authenticated(),
                    }
                else:
                    raise HTTPException(
                        status_code=500, detail="Google auth manager not initialized"
                    )
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/auth/status")
        async def auth_status() -> Dict[str, Any]:
            """Get authentication status."""
            google_status = (
                self.google_auth.get_auth_status()
                if self.google_auth
                else {
                    "authenticated": False,
                    "has_credentials": False,
                    "credentials_valid": False,
                    "gmail_service_available": False,
                    "calendar_service_available": False,
                }
            )

            return {
                "auth_initialized": self.auth_initialized,
                "google": google_status,
            }

        @self.app.get("/oauth2/callback")
        async def oauth_callback(request: Request) -> str:
            """Handle OAuth2 callback from Google."""
            code = request.query_params.get("code")
            error = request.query_params.get("error")
            state = request.query_params.get("state")

            if error:
                self.oauth_results["error"] = error
                # Signal that we received the callback
                if self.oauth_event:
                    self.oauth_event.set()
                return f"<html><body><h1>Error</h1><p>{error}</p></body></html>"
            elif code:
                self.oauth_results["code"] = code
                self.oauth_results["state"] = state
                # Signal that we received the callback
                if self.oauth_event:
                    self.oauth_event.set()
                return "<html><body><h1>Success</h1><p>Authentication successful!</p></body></html>"
            else:
                self.oauth_results["error"] = "No authorization code received"
                # Signal that we received the callback
                if self.oauth_event:
                    self.oauth_event.set()
                return "<html><body><h1>Error</h1><p>No authorization code received</p></body></html>"

    async def _initialize_auth(self) -> None:
        """Initialize authentication components (non-blocking)."""
        try:
            self.logger.info("🔐 Initializing authentication components...")

            # Load full Jarvis config
            self.jarvis_config = JarvisConfig()

            # Initialize Google auth manager
            self.google_auth = GoogleAuthManager(
                self.jarvis_config.google, mcp_server=self
            )

            # Add tool packages to path
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent

            gmail_path = project_root / "packages" / "tools" / "gmail-tool"
            calendar_path = project_root / "packages" / "tools" / "calendar-tool"
            notification_path = (
                project_root / "packages" / "tools" / "notification-tool"
            )
            hue_path = project_root / "packages" / "tools" / "hue-tool"

            for path in [gmail_path, calendar_path, notification_path, hue_path]:
                if str(path) not in sys.path:
                    sys.path.insert(0, str(path))

            # Initialize tool instances
            self.gmail_tool = GmailTool(self.jarvis_config.google)
            self.calendar_tool = CalendarTool(self.jarvis_config.google)
            self.notification_tool = NotificationTool()
            self.hue_tool = HueTool(self.jarvis_config.hue)

            # Register tools
            self._register_tools()

            self.auth_initialized = True
            self.logger.info("✅ Authentication components initialized successfully")

            # Auto-authenticate if credentials exist (non-blocking)
            if self.jarvis_config.google.credentials_file and os.path.exists(
                self.jarvis_config.google.credentials_file
            ):
                try:
                    success = await self.google_auth.authenticate()
                    if success:
                        await self._update_tools_with_auth()
                        self.logger.info("✅ Google authentication successful")
                    else:
                        self.logger.warning(
                            "⚠️ Google authentication failed, but server continues"
                        )
                except Exception as auth_error:
                    self.logger.warning(
                        f"⚠️ Google authentication error (non-blocking): {auth_error}"
                    )
            else:
                self.logger.info(
                    "ℹ️ No Google credentials found, authentication will be required on first use"
                )

        except Exception as e:
            self.logger.error(
                f"❌ Auth initialization failed (non-blocking): {e}", exc_info=True
            )
            # Don't raise - let server continue without auth
            self.auth_initialized = False

    def _register_tools(self) -> None:
        """Register all tools with the server."""
        # Register Gmail tools
        if self.gmail_tool:
            for tool_def in self.gmail_tool.get_tool_definitions():
                self.tools_registry[tool_def["name"]] = tool_def

        # Register Calendar tools
        if self.calendar_tool:
            for tool_def in self.calendar_tool.get_tool_definitions():
                self.tools_registry[tool_def["name"]] = tool_def

        # Register Notification tools
        if self.notification_tool:
            for tool_def in self.notification_tool.get_tool_definitions():
                self.tools_registry[tool_def["name"]] = tool_def

        # Register Hue tools
        if self.hue_tool:
            for tool_def in self.hue_tool.get_tool_definitions():
                self.tools_registry[tool_def["name"]] = tool_def

        self.logger.info(f"Registered {len(self.tools_registry)} tools")

    async def _update_tools_with_auth(self) -> None:
        """Update tool clients with authenticated services."""
        if not self.google_auth or not self.google_auth.is_authenticated():
            return

        try:
            gmail_service = self.google_auth.get_gmail_service()
            calendar_service = self.google_auth.get_calendar_service()

            self.logger.debug(f"Gmail service: {gmail_service}")
            self.logger.debug(f"Calendar service: {calendar_service}")

            if self.gmail_tool and gmail_service:
                # Ensure the Gmail tool client is initialized
                if not self.gmail_tool.client:
                    from jarvis_gmail.gmail_tool import GmailTool as OriginalGmailTool

                    self.gmail_tool.client = OriginalGmailTool(
                        self.jarvis_config.google
                    )

                # Update the Gmail client with authenticated service
                self.gmail_tool.client.client.set_service(
                    gmail_service, self.google_auth.credentials
                )
            else:
                self.logger.error("Gmail service not initialized")

            if self.calendar_tool and calendar_service:
                # Initialize client if not already done
                if not self.calendar_tool.client:
                    from jarvis_calendar.calendar_tool import (
                        CalendarTool as OriginalCalendarTool,
                    )

                    self.calendar_tool.client = OriginalCalendarTool(
                        self.jarvis_config.google
                    )
                    # Update the Calendar client with authenticated service
                    self.calendar_tool.client.client.set_service(
                        calendar_service, self.google_auth.credentials
                    )
            else:
                self.logger.error("Calendar service not initialized")
        except Exception as e:
            self.logger.error(f"Failed to update tools with auth: {e}")

    async def _execute_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool using the appropriate tool class."""
        try:
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

            elif tool_name.startswith("hue_"):
                if self.hue_tool:
                    return await self.hue_tool.execute(tool_name, arguments)
                else:
                    return {
                        "status": "error",
                        "message": "Hue tool not initialized",
                    }

            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        except Exception as e:
            self.logger.error(
                f"Tool execution failed for {tool_name}: {e}", exc_info=True
            )
            return {"status": "error", "message": str(e)}

    async def start_server(self) -> None:
        """Start the MCP Orchestrator server."""
        import uvicorn

        self.logger.info("Starting MCP Orchestrator Server")

        # Start server first
        config = uvicorn.Config(
            self.app, host=self.config.host, port=self.config.port, log_level="info"
        )
        server = uvicorn.Server(config)

        # Start authentication in background (non-blocking)
        auth_task = asyncio.create_task(self._initialize_auth())

        try:
            await server.serve()
        finally:
            # Cancel auth task if server stops
            if not auth_task.done():
                auth_task.cancel()
                try:
                    await auth_task
                except asyncio.CancelledError:
                    pass

    async def wait_for_oauth_callback(self, timeout: int = 300) -> Dict[str, Any]:
        """Wait for OAuth2 callback and return the result."""
        self.logger.info(f"🔄 Waiting for OAuth callback (timeout: {timeout}s)")
        self.oauth_event = asyncio.Event()
        self.oauth_results.clear()

        try:
            # Wait for the callback with timeout
            await asyncio.wait_for(self.oauth_event.wait(), timeout=timeout)
            self.logger.info("✅ OAuth callback received within timeout")
            return self.oauth_results.copy()
        except asyncio.TimeoutError:
            self.logger.error(f"❌ OAuth callback timeout after {timeout}s")
            return {"error": "OAuth callback timeout"}
        finally:
            self.oauth_event = None
            self.oauth_results.clear()
