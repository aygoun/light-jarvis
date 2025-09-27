#!/usr/bin/env python3
"""Start the Main Orchestrator server."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jarvis_shared.config import JarvisConfig
from jarvis_main_orchestrator import MainOrchestratorServer


async def main():
    """Start the Main Orchestrator server."""
    print("🤖 Starting Main Orchestrator Server...")

    # Load configuration
    config = JarvisConfig()

    # Create and start server
    server = MainOrchestratorServer(config)
    await server.start_server(host="localhost", port=3002)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Main Orchestrator Server stopped")
    except Exception as e:
        print(f"❌ Error starting Main Orchestrator Server: {e}")
        sys.exit(1)
