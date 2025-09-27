"""CLI for Jarvis Main Orchestrator."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from jarvis_shared.config import JarvisConfig
from jarvis_shared.logger import get_logger

from .assistant import JarvisAssistant

app = typer.Typer(help="Jarvis Main Orchestrator CLI")
console = Console()
logger = get_logger("jarvis.cli")


@app.command()
def chat(
    message: str = typer.Argument(..., help="Message to send to Jarvis"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream the response"),
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c", help="Config file path"
    ),
):
    """Chat with Jarvis."""
    asyncio.run(_chat_command(message, stream, config_file))


@app.command()
def server(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(3002, "--port", "-p", help="Port to bind to"),
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c", help="Config file path"
    ),
):
    """Start the Jarvis server."""
    asyncio.run(_server_command(host, port, config_file))


async def _chat_command(message: str, stream: bool, config_file: Optional[str]) -> None:
    """Handle chat command."""
    try:
        # Load config
        config = JarvisConfig()
        if config_file:
            # TODO: Load from specific config file
            pass

        # Initialize assistant
        assistant = JarvisAssistant(config)
        await assistant.initialize()

        # Display welcome message
        console.print(
            Panel(
                Text("🤖 Jarvis Assistant", style="bold blue"),
                title="Welcome",
                border_style="blue",
            )
        )

        if stream:
            # Stream response
            console.print(f"[bold]You:[/bold] {message}")
            console.print("[bold]Jarvis:[/bold] ", end="")

            async for token in assistant.process_command_stream(message):
                console.print(token, end="")
            console.print()  # New line after streaming
        else:
            # Regular response
            console.print(f"[bold]You:[/bold] {message}")
            response = await assistant.process_command(message)
            console.print(f"[bold]Jarvis:[/bold] {response}")

        # Cleanup
        await assistant.shutdown()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Chat command failed: {e}", exc_info=True)
        raise typer.Exit(1)


async def _server_command(host: str, port: int, config_file: Optional[str]) -> None:
    """Handle server command."""
    try:
        # Load config
        config = JarvisConfig()
        if config_file:
            # TODO: Load from specific config file
            pass

        # Display startup message
        console.print(
            Panel(
                Text("🚀 Starting Jarvis Main Orchestrator Server", style="bold green"),
                title="Jarvis Server",
                border_style="green",
            )
        )
        console.print(f"🌐 Server will be available at: http://{host}:{port}")
        console.print("📊 Health check: http://{host}:{port}/health")
        console.print("💬 Chat endpoint: http://{host}:{port}/chat")
        console.print("🎤 STT endpoint: http://{host}:{port}/stt/transcribe")
        console.print("🔊 TTS endpoint: http://{host}:{port}/tts/speak")
        console.print()

        # Start server
        from .server import MainOrchestratorServer

        server = MainOrchestratorServer(config)
        await server.start_server(host=host, port=port)

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down server...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.error(f"Server command failed: {e}", exc_info=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
