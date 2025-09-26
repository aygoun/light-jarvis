"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis_shared.config import OllamaConfig, MCPConfig, GoogleConfig, JarvisConfig


class TestOllamaConfig:
    """Test OllamaConfig model."""

    def test_default_config(self):
        """Test default Ollama configuration."""
        config = OllamaConfig()

        assert config.host == "http://localhost:11434"
        assert config.model == "llama3.2:3b"
        assert config.temperature == 0.1
        assert config.timeout == 120

    def test_custom_config(self):
        """Test custom Ollama configuration."""
        config = OllamaConfig(
            host="http://remote:11434", model="llama3.1:8b", temperature=0.5, timeout=60
        )

        assert config.host == "http://remote:11434"
        assert config.model == "llama3.1:8b"
        assert config.temperature == 0.5
        assert config.timeout == 60


class TestMCPConfig:
    """Test MCPConfig model."""

    def test_default_config(self):
        """Test default MCP configuration."""
        config = MCPConfig()

        assert config.host == "localhost"
        assert config.port == 3000  # Updated to match TOML
        assert config.timeout == 30

    def test_custom_config(self):
        """Test custom MCP configuration."""
        config = MCPConfig(host="0.0.0.0", port=9000, timeout=60)

        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.timeout == 60


class TestGoogleConfig:
    """Test GoogleConfig model."""

    def test_default_config(self):
        """Test default Google configuration."""
        config = GoogleConfig()

        assert config.credentials_file is None
        assert config.token_file is None
        assert (
            len(config.scopes) == 3
        )  # Updated to match TOML (gmail.send is commented out)
        assert "https://www.googleapis.com/auth/gmail.readonly" in config.scopes
        assert "https://www.googleapis.com/auth/calendar.events" in config.scopes

    def test_custom_config(self):
        """Test custom Google configuration."""
        custom_scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
        config = GoogleConfig(
            credentials_file="/path/to/creds.json",
            token_file="/path/to/token.json",
            scopes=custom_scopes,
        )

        assert config.credentials_file == "/path/to/creds.json"
        assert config.token_file == "/path/to/token.json"
        assert config.scopes == custom_scopes


class TestJarvisConfig:
    """Test JarvisConfig with environment variables."""

    def test_default_config(self):
        """Test default Jarvis configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(Path, "home", return_value=Path(temp_dir)):
                config = JarvisConfig()

                assert config.general.debug is False
                assert config.general.log_level == "DEBUG"  # From TOML
                assert config.ollama.model == "llama3.2:3b"
                assert config.mcp.port == 3000  # From TOML
                assert config.config_dir.name == ".jarvis"
                assert config.data_dir.name == "data"

    def test_environment_variables(self):
        """Test configuration from environment variables."""
        env_vars = {
            "JARVIS_GENERAL__DEBUG": "true",
            "JARVIS_GENERAL__LOG_LEVEL": "DEBUG",
            "JARVIS_OLLAMA__MODEL": "llama3.1:8b",
            "JARVIS_OLLAMA__TEMPERATURE": "0.5",
            "JARVIS_MCP__PORT": "9000",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch.object(Path, "home", return_value=Path(temp_dir)):
                    config = JarvisConfig()

                    assert config.general.debug is True
                    assert config.general.log_level == "DEBUG"
                    assert config.ollama.model == "llama3.1:8b"
                    assert config.ollama.temperature == 0.5
                    assert config.mcp.port == 9000

    def test_directory_creation(self):
        """Test that configuration directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(Path, "home", return_value=Path(temp_dir)):
                config = JarvisConfig()

                assert config.config_dir.exists()
                assert config.data_dir.exists()
                assert config.config_dir.is_dir()
                assert config.data_dir.is_dir()

    def test_google_credentials_paths(self):
        """Test Google credentials path setting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(Path, "home", return_value=Path(temp_dir)):
                config = JarvisConfig()

                expected_creds = str(config.config_dir / "google_credentials.json")
                expected_token = str(config.config_dir / "google_token.json")

                # TOML config sets these to ~/.jarvis paths, so we check for that
                assert "google_credentials.json" in config.google.credentials_file
                assert "google_token.json" in config.google.token_file

    def test_nested_config_env_vars(self):
        """Test nested configuration via environment variables."""
        env_vars = {
            "JARVIS_OLLAMA__HOST": "http://custom:11434",
            "JARVIS_OLLAMA__MODEL": "custom:7b",
            "JARVIS_MCP__HOST": "custom-mcp",
            "JARVIS_MCP__PORT": "7000",
        }

        with patch.dict(os.environ, env_vars):
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch.object(Path, "home", return_value=Path(temp_dir)):
                    config = JarvisConfig()

                    assert config.ollama.host == "http://custom:11434"
                    assert config.ollama.model == "custom:7b"
                    assert config.mcp.host == "custom-mcp"
                    assert config.mcp.port == 7000
