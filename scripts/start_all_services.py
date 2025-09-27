#!/usr/bin/env python3
"""Start all Jarvis services."""

import asyncio
import sys
import signal
from pathlib import Path
from typing import List

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jarvis_shared.config import JarvisConfig
from jarvis_mcp_orchestrator import MCPOrchestratorServer
from jarvis_whisper_service import WhisperServiceServer
from jarvis_main_orchestrator import MainOrchestratorServer


def print_with_service(service_name: str, message: str):
    """Print message with service prefix."""
    print(f"[{service_name}] {message}")


class ServiceManager:
    """Manages all Jarvis services."""

    def __init__(self):
        self.config = JarvisConfig()
        self.services: List[asyncio.Task] = []
        self.running = True

    async def start_mcp_orchestrator(self):
        """Start MCP Orchestrator service."""
        print_with_service("MCP-ORCHESTRATOR", "🚀 Starting MCP Orchestrator Server...")
        server = MCPOrchestratorServer(self.config.mcp)
        await server.start_server()

    async def start_whisper_service(self):
        """Start Whisper Service."""
        print_with_service("WHISPER-SERVICE", "🎤 Starting Whisper Service Server...")
        server = WhisperServiceServer(self.config.whisper, self.config.tts)
        await server.start_server(host="localhost", port=3001)

    async def start_main_orchestrator(self):
        """Start Main Orchestrator service."""
        print_with_service(
            "MAIN-ORCHESTRATOR", "🤖 Starting Main Orchestrator Server..."
        )
        server = MainOrchestratorServer(self.config)
        await server.start_server(host="localhost", port=3002)

    async def start_all_services(self):
        """Start all services concurrently."""
        print("=" * 60)
        print("🚀 STARTING JARVIS SERVICES")
        print("=" * 60)
        print("📋 Services:")
        print("  • MCP Orchestrator (port 3000) - Consolidates all MCP tools")
        print("  • Whisper Service (port 3001) - STT/TTS functionality")
        print("  • Main Orchestrator (port 3002) - Coordinates everything")
        print("=" * 60)
        print()

        # Start all services concurrently
        self.services = [
            asyncio.create_task(self.start_mcp_orchestrator()),
            asyncio.create_task(self.start_whisper_service()),
            asyncio.create_task(self.start_main_orchestrator()),
        ]

        try:
            # Wait for all services to complete
            await asyncio.gather(*self.services)
        except asyncio.CancelledError:
            print("\n👋 Shutting down all services...")
            # Cancel all remaining tasks
            for task in self.services:
                if not task.done():
                    task.cancel()
            # Wait for cancellation to complete
            await asyncio.gather(*self.services, return_exceptions=True)
            print("✅ All services stopped")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        # Cancel all tasks
        for task in self.services:
            if not task.done():
                task.cancel()


async def main():
    """Main entry point."""
    manager = ServiceManager()

    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)

    try:
        await manager.start_all_services()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 All services stopped")
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        sys.exit(1)
