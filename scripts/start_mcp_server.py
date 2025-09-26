#!/usr/bin/env python3
"""Start the Jarvis MCP server."""

import asyncio
import sys
from pathlib import Path

# Add packages to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "shared"))
sys.path.insert(0, str(project_root / "packages" / "mcp-server"))

from jarvis_shared.config import JarvisConfig
from jarvis_mcp import MCPServer


async def main():
    """Start the MCP server."""
    print("🚀 Starting Jarvis MCP Server...")

    # Load configuration
    config = JarvisConfig()

    # Create and start server
    server = MCPServer(config.mcp)
    await server.start_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
