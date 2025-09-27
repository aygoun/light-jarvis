"""Jarvis CLI application."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live
from rich.text import Text

from jarvis_core import JarvisAssistant
from jarvis_shared.config import JarvisConfig
from jarvis_shared.logger import get_logger

app = typer.Typer(
    name="jarvis", help="Jarvis AI Assistant - Your personal AI assistant"
)
console = Console()


@app.command()
def chat(
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Ollama model to use"
    ),
    config_dir: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Configuration directory"
    ),
    no_stream: bool = typer.Option(
        False, "--no-stream", help="Disable streaming and show full response at once"
    ),
):
    """Start interactive chat with Jarvis."""

    # Load configuration
    config = JarvisConfig()
    if model:
        config.ollama.model = model
    if config_dir:
        config.config_dir = config_dir

    console.print(
        Panel.fit(
            f"🤖 [bold blue]Jarvis AI Assistant[/bold blue]\n"
            f"Model: {config.ollama.model}\n"
            f"Type 'quit' or 'exit' to end the conversation.",
            title="Welcome",
        )
    )

    # Run async chat
    asyncio.run(_async_chat(config, not no_stream))


async def _async_chat(config: JarvisConfig, use_streaming: bool = True):
    """Async chat loop."""

    # Initialize logger and assistant
    logger = get_logger("jarvis.cli")
    logger.info("🚀 Starting Jarvis CLI chat session")
    assistant = JarvisAssistant(config)

    try:
        console.print("🔄 Initializing Jarvis...")
        await assistant.initialize()
        console.print("✅ Jarvis is ready!")

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You[/bold green]")

                if user_input.lower() in ["quit", "exit", "bye"]:
                    console.print("👋 Goodbye!")
                    break

                if user_input.lower() == "clear":
                    assistant.clear_conversation()
                    console.print("🧹 Conversation cleared!")
                    continue

                # Process command
                console.print("🤔 [italic]Jarvis is thinking...[/italic]")

                if use_streaming:
                    # Streaming mode - show tokens in real-time
                    response_text = Text()
                    response_text.append("Jarvis", style="bold blue")
                    response_text.append(": ")

                    # Use Rich Live to update display in real-time
                    with Live(
                        response_text, console=console, refresh_per_second=10
                    ) as live:
                        full_response = ""
                        try:
                            async for token in assistant.process_command_stream(
                                user_input
                            ):
                                full_response += token
                                # Update the display with new token
                                updated_text = Text()
                                updated_text.append("Jarvis", style="bold blue")
                                updated_text.append(": ")
                                updated_text.append(full_response)
                                live.update(updated_text)
                        except Exception as e:
                            # Fallback to non-streaming if streaming fails
                            console.print(
                                f"\n⚠️  Streaming failed, falling back to standard mode: {e}"
                            )
                            response = await assistant.process_command(user_input)
                            updated_text = Text()
                            updated_text.append("Jarvis", style="bold blue")
                            updated_text.append(": ")
                            updated_text.append(response)
                            live.update(updated_text)

                    # Final newline after streaming is complete
                    console.print()
                else:
                    # Non-streaming mode - show complete response at once
                    response = await assistant.process_command(user_input)
                    console.print(f"\n[bold blue]Jarvis[/bold blue]: {response}")

            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"❌ Error: {e}")
                if config.general.debug:
                    console.print_exception()

    finally:
        await assistant.shutdown()


@app.command()
def setup():
    """Set up Jarvis configuration and credentials."""
    console.print("🔧 Setting up Jarvis...")

    config = JarvisConfig()

    # Create config directory
    config.config_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"📁 Configuration directory: {config.config_dir}")
    console.print(f"📊 Data directory: {config.data_dir}")

    # Check Ollama connection
    from jarvis_llm import LLMService

    llm_service = LLMService(config.ollama)

    try:
        models = llm_service.get_available_models()
        console.print(f"✅ Ollama connected. Available models: {', '.join(models)}")

        if config.ollama.model not in [model.split(":")[0] for model in models]:
            console.print(f"⚠️  Model '{config.ollama.model}' not found.")
            if typer.confirm(f"Would you like to pull '{config.ollama.model}'?"):
                console.print(f"📥 Pulling {config.ollama.model}...")
                if llm_service.pull_model(config.ollama.model):
                    console.print("✅ Model pulled successfully!")
                else:
                    console.print("❌ Failed to pull model.")
    except Exception as e:
        console.print(f"❌ Cannot connect to Ollama: {e}")
        console.print("Make sure Ollama is running: `ollama serve`")

    # Google credentials setup
    creds_file = Path(config.google.credentials_file)
    if not creds_file.exists():
        console.print(f"\n📧 Google credentials not found at: {creds_file}")
        console.print("To set up Gmail and Calendar integration:")
        console.print("1. Go to Google Cloud Console")
        console.print("2. Create a new project or select existing")
        console.print("3. Enable Gmail and Calendar APIs")
        console.print("4. Create OAuth 2.0 credentials")
        console.print(f"5. Download credentials.json to: {creds_file}")
    else:
        console.print("✅ Google credentials found!")

    console.print("\n🎉 Setup complete! Run 'jarvis chat' to start.")


@app.command()
def status():
    """Check Jarvis system status."""
    console.print("🔍 Checking Jarvis status...")

    config = JarvisConfig()

    # Check Ollama
    from jarvis_llm import LLMService

    llm_service = LLMService(config.ollama)

    try:
        models = llm_service.get_available_models()
        console.print(
            f"✅ Ollama: Connected {len(models)} models available:", ", ".join(models)
        )
    except Exception as e:
        console.print(f"❌ Ollama: {e}")

    # Check Google credentials
    creds_file = Path(config.google.credentials_file)
    if creds_file.exists():
        console.print("✅ Google: Credentials found")
    else:
        console.print("⚠️  Google: Credentials not configured")

    # Check config
    console.print(f"📁 Config: {config.config_dir}")
    console.print(f"🤖 Model: {config.ollama.model}")


if __name__ == "__main__":
    app()
