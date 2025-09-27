#!/usr/bin/env python3
"""Main Jarvis entry point script."""

import asyncio
import sys
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jarvis_shared.config import JarvisConfig
from jarvis_main_orchestrator import JarvisAssistant


async def chat_mode(message: str, stream: bool = False):
    """Run Jarvis in chat mode."""
    try:
        # Load configuration
        config = JarvisConfig()
        
        # Initialize assistant
        assistant = JarvisAssistant(config)
        await assistant.initialize()
        
        if stream:
            # Stream response
            print(f"You: {message}")
            print("Jarvis: ", end="", flush=True)
            
            async for token in assistant.process_command_stream(message):
                print(token, end="", flush=True)
            print()  # New line after streaming
        else:
            # Regular response
            print(f"You: {message}")
            response = await assistant.process_command(message)
            print(f"Jarvis: {response}")
        
        # Cleanup
        await assistant.shutdown()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


async def server_mode(host: str = "localhost", port: int = 3002):
    """Run Jarvis in server mode."""
    try:
        from jarvis_main_orchestrator import MainOrchestratorServer
        
        # Load configuration
        config = JarvisConfig()
        
        # Create and start server
        server = MainOrchestratorServer(config)
        await server.start_server(host=host, port=port)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Jarvis AI Assistant")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with Jarvis")
    chat_parser.add_argument("message", help="Message to send to Jarvis")
    chat_parser.add_argument("--stream", "-s", action="store_true", help="Stream the response")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start Jarvis server")
    server_parser.add_argument("--host", "-h", default="localhost", help="Host to bind to")
    server_parser.add_argument("--port", "-p", type=int, default=3002, help="Port to bind to")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test Jarvis integration")
    
    args = parser.parse_args()
    
    if args.command == "chat":
        asyncio.run(chat_mode(args.message, args.stream))
    elif args.command == "server":
        asyncio.run(server_mode(args.host, args.port))
    elif args.command == "test":
        from test_integration import test_basic_functionality
        asyncio.run(test_basic_functionality())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
