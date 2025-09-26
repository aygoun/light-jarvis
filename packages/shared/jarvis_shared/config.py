"""Configuration management for Jarvis."""

import toml
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
    model: str = "llama3.2:3b"
    temperature: float = 0.1
    timeout: int = 120


class MCPConfig(BaseModel):
    """MCP server configuration."""

    host: str = "localhost"
    port: int = 3000
    timeout: int = 30


class GoogleConfig(BaseModel):
    """Google services configuration."""

    credentials_file: Optional[str] = None
    token_file: Optional[str] = None
    oauth_callback_host: str = "localhost"
    oauth_callback_port: int = 3000  # Same port as MCP server
    oauth_callback_path: str = "/oauth2/callback"
    scopes: list[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/gmail.readonly",
            # "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/calendar.events",
        ]
    )

    @property
    def oauth_callback_url(self) -> str:
        """Get the full OAuth2 callback URL."""
        return f"http://{self.oauth_callback_host}:{self.oauth_callback_port}{self.oauth_callback_path}"


class GeneralConfig(BaseModel):
    """General configuration."""

    debug: bool = False
    log_level: str = "INFO"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    dir: str = "./logs"
    console: bool = False
    file: bool = True
    rich: bool = True
    max_size: int = 10485760  # 10MB
    backup_count: int = 5
    date_format: str = "%Y-%m-%d %H:%M:%S"


class JarvisConfig(BaseSettings):
    """Main Jarvis configuration."""

    # Paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".jarvis")
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".jarvis" / "data")

    # Services
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    google: GoogleConfig = Field(default_factory=GoogleConfig)

    # Configuration sections
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_prefix = "JARVIS_"
        env_file = ".env"
        env_nested_delimiter = "__"

    def __init__(self, **kwargs):
        # Load configuration from TOML file
        toml_config = self._load_toml_config()

        # Merge TOML config with kwargs (kwargs take precedence over TOML)
        if toml_config:
            # Deep merge TOML config with kwargs
            merged_config = self._deep_merge(toml_config, kwargs)
            kwargs = merged_config

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

    def _load_toml_config(self) -> dict:
        """Load configuration from default.toml file."""
        try:
            toml_path = Path("config/default.toml")
            if toml_path.exists():
                with open(toml_path, "r") as f:
                    return toml.load(f)
        except Exception as e:
            print(f"Warning: Could not load TOML config: {e}")
        return {}

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
