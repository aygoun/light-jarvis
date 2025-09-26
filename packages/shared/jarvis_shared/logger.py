"""Advanced logging system for Jarvis with environment-based configuration."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from enum import Enum

from rich.console import Console
from rich.logging import RichHandler


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
        self,
        name: str = "jarvis",
        log_level: Optional[str] = None,
        log_dir: Optional[Path] = None,
        console_output: Optional[bool] = None,
        file_output: Optional[bool] = None,
        rich_formatting: Optional[bool] = None,
    ):
        self.name = name
        self.console = Console()

        # Environment variable configuration with defaults
        self.log_level = LogLevel(
            log_level or os.getenv("JARVIS_LOG_LEVEL", "INFO").upper()
        )

        log_dir_env = os.getenv("JARVIS_LOG_DIR")
        if log_dir is not None:
            self.log_dir = Path(log_dir)
        elif log_dir_env is not None:
            self.log_dir = Path(log_dir_env)
        else:
            self.log_dir = Path.cwd() / "logs"

        self.console_output = (
            console_output
            if console_output is not None
            else os.getenv("JARVIS_LOG_CONSOLE", "false").lower() == "true"
        )

        self.file_output = (
            file_output
            if file_output is not None
            else os.getenv("JARVIS_LOG_FILE", "true").lower() == "true"
        )

        self.rich_formatting = (
            rich_formatting
            if rich_formatting is not None
            else os.getenv("JARVIS_LOG_RICH", "true").lower() == "true"
        )

        # Additional configuration
        self.max_file_size = int(os.getenv("JARVIS_LOG_MAX_SIZE", "10485760"))  # 10MB
        self.backup_count = int(os.getenv("JARVIS_LOG_BACKUP_COUNT", "5"))
        self.date_format = os.getenv("JARVIS_LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")

        # Setup logger
        self.logger = self._setup_logger()

    @classmethod
    def get_logger(cls, name: str = "jarvis", **kwargs) -> "JarvisLogger":
        """Get or create a logger instance (singleton per name)."""
        if name not in cls._instances:
            cls._instances[name] = cls(name, **kwargs)
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

    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """Log function calls for debugging."""
        kwargs = kwargs or {}
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        params = ", ".join(filter(None, [args_str, kwargs_str]))
        self.debug(f"🔧 Calling {func_name}({params})")

    def log_performance(self, operation: str, duration: float, **metadata):
        """Log performance metrics."""
        meta_str = " | ".join([f"{k}={v}" for k, v in metadata.items()])
        self.info(f"⏱️  {operation} completed in {duration:.3f}s | {meta_str}")

    def log_api_call(self, method: str, url: str, status_code: int, duration: float):
        """Log API calls."""
        status_emoji = "✅" if 200 <= status_code < 300 else "❌"
        self.info(f"{status_emoji} {method} {url} -> {status_code} ({duration:.3f}s)")

    def log_tool_execution(
        self, tool_name: str, success: bool, duration: float, **metadata
    ):
        """Log tool executions."""
        status_emoji = "✅" if success else "❌"
        meta_str = " | ".join([f"{k}={v}" for k, v in metadata.items()])
        self.info(
            f"{status_emoji} Tool '{tool_name}' executed in {duration:.3f}s | {meta_str}"
        )

    def structured_log(self, level: str, event: str, **data):
        """Log structured data for analysis."""
        log_data = {"event": event, "timestamp": datetime.utcnow().isoformat(), **data}
        log_method = getattr(self.logger, level.lower())
        log_method(f"📊 {event} | {log_data}")

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
def get_logger(name: str = "jarvis", **kwargs) -> JarvisLogger:
    """Get a Jarvis logger instance."""
    return JarvisLogger.get_logger(name, **kwargs)


# Default logger instance
logger = get_logger()


# Decorator for automatic function logging
def log_calls(logger_name: str = "jarvis"):
    """Decorator to automatically log function calls."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            log = get_logger(logger_name)
            log.log_function_call(func.__name__, args, kwargs)
            try:
                start_time = datetime.now()
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                log.log_performance(f"{func.__name__}", duration)
                return result
            except Exception as e:
                log.error(f"Error in {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


# Context manager for performance logging
class LogPerformance:
    """Context manager for logging operation performance."""

    def __init__(self, operation: str, logger_name: str = "jarvis", **metadata):
        self.operation = operation
        self.logger = get_logger(logger_name)
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
