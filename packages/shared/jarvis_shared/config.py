"""Configuration management for Jarvis."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # type: ignore


class OllamaConfig(BaseModel):
    """Ollama configuration."""

    host: str = "http://localhost:11434"
    model: str = "mistral:7b"
    temperature: float = 0.1
    timeout: int = 120


class MCPConfig(BaseModel):
    """MCP server configuration."""

    host: str = "localhost"
    port: int = 8000
    timeout: int = 30


class GoogleConfig(BaseModel):
    """Google services configuration."""

    credentials_file: Optional[str] = None
    token_file: Optional[str] = None
    scopes: list[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events",
        ]
    )


class JarvisConfig(BaseSettings):
    """Main Jarvis configuration."""

    # Paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".jarvis")
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".jarvis" / "data")

    # Services
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    google: GoogleConfig = Field(default_factory=GoogleConfig)

    # General
    debug: bool = False
    log_level: str = "INFO"

    class Config:
        env_prefix = "JARVIS_"
        env_file = ".env"
        env_nested_delimiter = "__"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Set default Google credentials path
        if not self.google.credentials_file:
            self.google.credentials_file = str(
                self.config_dir / "google_credentials.json"
            )
        if not self.google.token_file:
            self.google.token_file = str(self.config_dir / "google_token.json")
