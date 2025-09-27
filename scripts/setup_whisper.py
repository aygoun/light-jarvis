#!/usr/bin/env python3
"""Setup script for Whisper.cpp integration."""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command: str, check: bool = True) -> bool:
    """Run a command and return success status."""
    try:
        print(f"Running: {command}")
        result = subprocess.run(
            command, shell=True, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def install_whisper_cpp():
    """Install Whisper.cpp."""
    print("🔧 Installing Whisper.cpp...")

    # Check if whisper.cpp already exists
    if os.path.exists("whisper.cpp"):
        print("✅ Whisper.cpp already exists")
        return True

    # Clone whisper.cpp
    if not run_command("git clone https://github.com/ggerganov/whisper.cpp.git"):
        print("❌ Failed to clone whisper.cpp")
        return False

    # Build whisper.cpp
    os.chdir("whisper.cpp")

    # Download the base English model
    if not run_command("sh ./models/download-ggml-model.sh base.en"):
        print("❌ Failed to download Whisper model")
        return False

    # Build with make (simpler approach)
    if not run_command("make"):
        print("❌ Failed to build whisper.cpp")
        return False

    # Go back to project root
    os.chdir("..")

    print("✅ Whisper.cpp installed successfully")
    return True


def download_whisper_model():
    """Download a Whisper model."""
    print("📥 Checking Whisper model...")

    # Check if model exists in whisper.cpp directory
    whisper_model_path = Path("whisper.cpp/models/ggml-base.en.bin")
    if whisper_model_path.exists():
        print("✅ Model already exists in whisper.cpp directory")

        # Create models directory in project root
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)

        # Copy model to project models directory
        import shutil

        shutil.copy2(whisper_model_path, models_dir / "ggml-base.en.bin")
        print("✅ Model copied to project models directory")
        return True

    # If not found, download it
    print("📥 Downloading Whisper model...")
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # Download base English model
    model_url = (
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
    )
    model_path = models_dir / "ggml-base.en.bin"

    if model_path.exists():
        print("✅ Model already exists")
        return True

    # Download model
    if not run_command(f"curl -L -o {model_path} {model_url}"):
        print("❌ Failed to download model")
        return False

    print("✅ Model downloaded successfully")
    return True


def setup_environment():
    """Setup environment variables."""
    print("🔧 Setting up environment...")

    env_file = Path(".env")
    env_content = """
# Whisper Configuration
JARVIS_WHISPER__MODEL_PATH=models/ggml-base.en.bin
JARVIS_WHISPER__WHISPER_CPP_PATH=whisper.cpp/main
JARVIS_WHISPER__LANGUAGE=en
JARVIS_WHISPER__TEMPERATURE=0.0
JARVIS_WHISPER__MAX_LEN=448

# TTS Configuration
JARVIS_TTS__ENGINE=edge
JARVIS_TTS__VOICE=en-US-AriaNeural
JARVIS_TTS__RATE=200
JARVIS_TTS__VOLUME=0.8
"""

    with open(env_file, "w") as f:
        f.write(env_content)

    print("✅ Environment file created")
    return True


def install_python_dependencies():
    """Install Python dependencies for voice services."""
    print("🐍 Installing Python dependencies...")

    # Install whisper service dependencies
    if not run_command("uv add jarvis-whisper jarvis-tts"):
        print("❌ Failed to install voice service dependencies")
        return False

    print("✅ Python dependencies installed")
    return True


def main():
    """Main setup function."""
    print("🚀 Setting up Whisper.cpp integration for Jarvis...")

    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Please run this script from the Jarvis project root")
        sys.exit(1)

    # Install dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        sys.exit(1)

    # Install Whisper.cpp
    if not install_whisper_cpp():
        print("❌ Failed to install Whisper.cpp")
        sys.exit(1)

    # Download model
    if not download_whisper_model():
        print("❌ Failed to download Whisper model")
        sys.exit(1)

    # Setup environment
    if not setup_environment():
        print("❌ Failed to setup environment")
        sys.exit(1)

    print("\n🎉 Whisper.cpp integration setup complete!")
    print("\nNext steps:")
    print("1. Start the MCP server: python -m jarvis_mcp.server")
    print("2. Start the web UI: cd ui/web && npm run dev")
    print("3. Open http://localhost:80 in your browser")
    print("\nVoice features:")
    print("- Click the microphone to record audio")
    print("- Toggle voice mode on/off")
    print("- Responses will be automatically spoken")


if __name__ == "__main__":
    main()
