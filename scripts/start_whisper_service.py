#!/usr/bin/env python3
"""Start the Whisper Service server."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jarvis_shared.config import JarvisConfig
from jarvis_whisper_service import WhisperServiceServer


async def main():
    """Start the Whisper Service server."""
    print("🎤 Starting Whisper Service Server...")

    # Load configuration
    config = JarvisConfig()

    # Create and start server
    server = WhisperServiceServer(config.whisper, config.tts)
    await server.start_server(host="localhost", port=3001)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Whisper Service Server stopped")
    except Exception as e:
        print(f"❌ Error starting Whisper Service Server: {e}")
        sys.exit(1)
