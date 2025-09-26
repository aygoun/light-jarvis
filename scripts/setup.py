"""Setup script for Jarvis development environment."""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, check: bool = True) -> bool:
    """Run a shell command."""
    try:
        result = subprocess.run(
            command, shell=True, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def main():
    """Set up Jarvis development environment."""
    print("🚀 Setting up Jarvis development environment...")

    # Check if uv is installed
    if not run_command("uv --version", check=False):
        print("❌ uv is not installed. Please install it first:")
        print("curl -LsSf https://astral.sh/uv/install.sh | sh")
        sys.exit(1)

    print("✅ uv found")

    # Install dependencies
    print("📦 Installing dependencies...")
    if not run_command("uv sync"):
        print("❌ Failed to install dependencies")
        sys.exit(1)

    print("✅ Dependencies installed")

    # Check if Ollama is running
    print("🔍 Checking Ollama...")
    if run_command("curl -s http://localhost:11434/api/tags", check=False):
        print("✅ Ollama is running")

        # Check if mistral model is available
        result = subprocess.run(
            "curl -s http://localhost:11434/api/tags | grep -q mistral",
            shell=True,
            check=False,
        )

        if result.returncode != 0:
            print("📥 Pulling Mistral model...")
            if not run_command("ollama pull llama3.2:3b"):
                print("⚠️  Failed to pull Mistral model, but continuing...")
        else:
            print("✅ Mistral model available")
    else:
        print("⚠️  Ollama is not running. Start it with: ollama serve")

    # Create config directory
    config_dir = Path.home() / ".jarvis"
    config_dir.mkdir(exist_ok=True)
    print(f"📁 Config directory created: {config_dir}")

    # Copy environment file
    env_example = Path("env.example")
    env_file = Path(".env")
    if env_example.exists() and not env_file.exists():
        env_file.write_text(env_example.read_text())
        print("📄 Environment file created")

    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. If Ollama isn't running: ollama serve")
    print("2. Run setup: uv run jarvis setup")
    print("3. Start chatting: uv run jarvis chat")
    print("\nFor Google integration, you'll need to:")
    print("1. Set up Google Cloud Console project")
    print("2. Enable Gmail and Calendar APIs")
    print("3. Download OAuth credentials to ~/.jarvis/google_credentials.json")


if __name__ == "__main__":
    main()
