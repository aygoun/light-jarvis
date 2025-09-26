"""Advanced logging system for Jarvis with TOML-based configuration."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from enum import Enum

from rich.console import Console
from rich.logging import RichHandler

from .config import JarvisConfig


class LogLevel(str, Enum):
    """Log levels for Jarvis."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class JarvisLogger:
    """Advanced logger for Jarvis with rich console output and file logging."""

    _instances: Dict[str, "JarvisLogger"] = {}

    def __init__(
        self, name: str = "jarvis", config: Optional[JarvisConfig] = None, **kwargs
    ):
        self.name = name
        self.console = Console()

        # Load configuration from TOML if not provided
        if config is None:
            config = JarvisConfig()

        # Use TOML configuration with fallback to environment variables
        self.log_level = LogLevel(
            kwargs.get("log_level")
            or config.general.log_level
            or os.getenv("JARVIS_LOG_LEVEL", "INFO").upper()
        )

        self.log_dir = Path(
            kwargs.get("log_dir")
            or config.logging.dir
            or os.getenv("JARVIS_LOG_DIR", "./logs")
        )

        self.console_output = kwargs.get(
            "console_output",
            (
                config.logging.console
                if hasattr(config.logging, "console")
                else os.getenv("JARVIS_LOG_CONSOLE", "false").lower() == "true"
            ),
        )

        self.file_output = kwargs.get(
            "file_output",
            (
                config.logging.file
                if hasattr(config.logging, "file")
                else os.getenv("JARVIS_LOG_FILE", "true").lower() == "true"
            ),
        )

        self.rich_formatting = kwargs.get(
            "rich_formatting",
            (
                config.logging.rich
                if hasattr(config.logging, "rich")
                else os.getenv("JARVIS_LOG_RICH", "true").lower() == "true"
            ),
        )

        # Additional configuration
        self.max_file_size = kwargs.get(
            "max_file_size",
            (
                config.logging.max_size
                if hasattr(config.logging, "max_size")
                else int(os.getenv("JARVIS_LOG_MAX_SIZE", "10485760"))
            ),
        )
        self.backup_count = kwargs.get(
            "backup_count",
            (
                config.logging.backup_count
                if hasattr(config.logging, "backup_count")
                else int(os.getenv("JARVIS_LOG_BACKUP_COUNT", "5"))
            ),
        )
        self.date_format = kwargs.get(
            "date_format",
            (
                config.logging.date_format
                if hasattr(config.logging, "date_format")
                else os.getenv("JARVIS_LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")
            ),
        )

        # Setup logger
        self.logger = self._setup_logger()

    @classmethod
    def get_logger(
        cls, name: str = "jarvis", config: Optional[JarvisConfig] = None, **kwargs
    ) -> "JarvisLogger":
        """Get or create a logger instance (singleton per name)."""
        if name not in cls._instances:
            cls._instances[name] = cls(name, config=config, **kwargs)
        return cls._instances[name]

    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with handlers."""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.log_level.value))

        # Clear existing handlers to avoid duplicates
        logger.handlers.clear()

        # Console handler with Rich formatting
        if self.console_output:
            if self.rich_formatting:
                console_handler: logging.Handler = RichHandler(
                    console=self.console,
                    show_time=True,
                    show_path=True,
                    enable_link_path=True,
                    markup=True,
                )
                console_handler.setFormatter(
                    logging.Formatter(
                        fmt="%(message)s",
                        datefmt=self.date_format,
                    )
                )
            else:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(
                    logging.Formatter(
                        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                        datefmt=self.date_format,
                    )
                )

            console_handler.setLevel(getattr(logging, self.log_level.value))
            logger.addHandler(console_handler)

        # File handler with date-based organization
        if self.file_output:
            file_handler = self._create_file_handler()
            if file_handler:
                logger.addHandler(file_handler)

        return logger

    def _create_file_handler(self) -> Optional[logging.Handler]:
        """Create file handler with date-based file organization."""
        try:
            # Create date-based directory structure
            today = datetime.now()
            date_dir = self.log_dir / today.strftime("%Y") / today.strftime("%m")
            date_dir.mkdir(parents=True, exist_ok=True)

            # Create log file with date-based name
            log_filename = f"{today.strftime('%Y_%m_%d')}_{self.name}.log"
            log_file = date_dir / log_filename

            # Use RotatingFileHandler for size management
            from logging.handlers import RotatingFileHandler

            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding="utf-8",
            )

            file_handler.setFormatter(
                logging.Formatter(
                    fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                    datefmt=self.date_format,
                )
            )

            file_handler.setLevel(getattr(logging, self.log_level.value))
            return file_handler

        except Exception as e:
            # Fallback: log to console if file logging fails
            self.console.print(f"[red]Failed to create file handler: {e}[/red]")
            return None

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)

    def log_performance(self, operation: str, duration: float, **metadata):
        """Log performance metrics."""
        meta_str = " | ".join([f"{k}={v}" for k, v in metadata.items()])
        self.info(f"⏱️  {operation} completed in {duration:.3f}s | {meta_str}")

    def log_tool_execution(
        self, tool_name: str, success: bool, duration: float, **metadata
    ):
        """Log tool executions."""
        status_emoji = "✅" if success else "❌"
        meta_str = " | ".join([f"{k}={v}" for k, v in metadata.items()])
        self.info(
            f"{status_emoji} Tool '{tool_name}' executed in {duration:.3f}s | {meta_str}"
        )

    def get_log_files(self) -> list[Path]:
        """Get list of current log files."""
        if not self.log_dir.exists():
            return []

        log_files = []
        for file_path in self.log_dir.rglob("*.log"):
            log_files.append(file_path)

        return sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up log files older than specified days."""
        if not self.log_dir.exists():
            return

        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        cleaned_count = 0

        for log_file in self.log_dir.rglob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    self.warning(f"Failed to delete old log file {log_file}: {e}")

        if cleaned_count > 0:
            self.info(f"🧹 Cleaned up {cleaned_count} old log files")

    def set_level(self, level: str):
        """Change log level at runtime."""
        self.log_level = LogLevel(level.upper())
        self.logger.setLevel(getattr(logging, self.log_level.value))
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, self.log_level.value))
        self.info(f"📝 Log level changed to {self.log_level.value}")


# Convenience functions for easy usage
def get_logger(
    name: str = "jarvis", config: Optional[JarvisConfig] = None, **kwargs
) -> JarvisLogger:
    """Get a Jarvis logger instance."""
    return JarvisLogger.get_logger(name, config=config, **kwargs)


# Default logger instance
logger = get_logger()


# Context manager for performance logging
class LogPerformance:
    """Context manager for logging operation performance."""

    def __init__(
        self,
        operation: str,
        logger_name: str = "jarvis",
        config: Optional[JarvisConfig] = None,
        **metadata,
    ):
        self.operation = operation
        self.logger = get_logger(logger_name, config=config)
        self.metadata = metadata
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"🚀 Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.log_performance(self.operation, duration, **self.metadata)
        else:
            self.logger.error(
                f"❌ {self.operation} failed after {duration:.3f}s: {exc_val}"
            )
        return False
