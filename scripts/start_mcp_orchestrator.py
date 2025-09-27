#!/usr/bin/env python3
"""Start the MCP Orchestrator server."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jarvis_shared.config import JarvisConfig
from jarvis_mcp_orchestrator import MCPOrchestratorServer


async def main():
    """Start the MCP Orchestrator server."""
    print("🚀 Starting MCP Orchestrator Server...")

    # Load configuration
    config = JarvisConfig()

    # Create and start server
    server = MCPOrchestratorServer(config.mcp)
    await server.start_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 MCP Orchestrator Server stopped")
    except Exception as e:
        print(f"❌ Error starting MCP Orchestrator Server: {e}")
        sys.exit(1)
