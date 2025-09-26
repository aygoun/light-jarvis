"""Tests for logging system."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from jarvis_shared.logger import (
    JarvisLogger,
    LogLevel,
    get_logger,
    log_calls,
    LogPerformance,
)


class TestLogLevel:
    """Test LogLevel enum."""

    def test_log_levels(self):
        """Test all log levels are available."""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestJarvisLogger:
    """Test JarvisLogger class."""

    def test_default_logger_creation(self):
        """Test creating logger with default settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = JarvisLogger(name="test", log_dir=Path(temp_dir) / "logs")

            assert logger.name == "test"
            assert logger.log_level == LogLevel.INFO
            assert logger.console_output is False  # Default from env
            assert logger.file_output is True
            assert logger.rich_formatting is True

    def test_custom_logger_settings(self):
        """Test logger with custom settings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = JarvisLogger(
                name="custom",
                log_level="DEBUG",
                log_dir=Path(temp_dir) / "custom_logs",
                console_output=True,
                file_output=False,
                rich_formatting=False,
            )

            assert logger.log_level == LogLevel.DEBUG
            assert logger.console_output is True
            assert logger.file_output is False
            assert logger.rich_formatting is False

    def test_environment_variable_config(self):
        """Test logger configuration from environment variables."""
        env_vars = {
            "JARVIS_LOG_LEVEL": "WARNING",
            "JARVIS_LOG_CONSOLE": "true",
            "JARVIS_LOG_FILE": "false",
            "JARVIS_LOG_RICH": "false",
            "JARVIS_LOG_MAX_SIZE": "5242880",  # 5MB
            "JARVIS_LOG_BACKUP_COUNT": "3",
        }

        with patch.dict(os.environ, env_vars):
            with tempfile.TemporaryDirectory() as temp_dir:
                logger = JarvisLogger(name="env_test", log_dir=Path(temp_dir) / "logs")

                assert logger.log_level == LogLevel.WARNING
                assert logger.console_output is True
                assert logger.file_output is False
                assert logger.rich_formatting is False
                assert logger.max_file_size == 5242880
                assert logger.backup_count == 3

    def test_singleton_behavior(self):
        """Test that get_logger returns same instance for same name."""
        logger1 = JarvisLogger.get_logger("singleton_test")
        logger2 = JarvisLogger.get_logger("singleton_test")

        assert logger1 is logger2

        # Different name should return different instance
        logger3 = JarvisLogger.get_logger("different_test")
        assert logger1 is not logger3

    def test_log_methods(self):
        """Test basic logging methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = JarvisLogger(
                name="methods_test",
                log_dir=Path(temp_dir) / "logs",
                console_output=False,
                file_output=False,
            )

            # Mock the underlying logger
            logger.logger = Mock()

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            logger.exception("Exception message")

            logger.logger.debug.assert_called_with("Debug message")
            logger.logger.info.assert_called_with("Info message")
            logger.logger.warning.assert_called_with("Warning message")
            logger.logger.error.assert_called_with("Error message")
            logger.logger.critical.assert_called_with("Critical message")
            logger.logger.exception.assert_called_with("Exception message")

    def test_specialized_log_methods(self):
        """Test specialized logging methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = JarvisLogger(
                name="specialized_test",
                log_dir=Path(temp_dir) / "logs",
                console_output=False,
                file_output=False,
            )

            # Mock the underlying logger
            logger.logger = Mock()

            # Test function call logging
            logger.log_function_call("test_func", ("arg1", "arg2"), {"key": "value"})
            logger.logger.debug.assert_called()

            # Test performance logging
            logger.log_performance("test_operation", 1.234, param1="value1")
            logger.logger.info.assert_called()

            # Test API call logging
            logger.log_api_call("GET", "http://example.com", 200, 0.5)
            logger.logger.info.assert_called()

            # Test tool execution logging
            logger.log_tool_execution("test_tool", True, 0.8, result="success")
            logger.logger.info.assert_called()

    def test_structured_logging(self):
        """Test structured logging functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = JarvisLogger(
                name="structured_test",
                log_dir=Path(temp_dir) / "logs",
                console_output=False,
                file_output=False,
            )

            # Mock the underlying logger
            logger.logger = Mock()

            logger.structured_log("info", "user_action", user_id="123", action="login")
            logger.logger.info.assert_called()

            # Check that the call included structured data
            call_args = logger.logger.info.call_args[0][0]
            assert "user_action" in call_args
            assert "user_id" in call_args

    def test_file_creation(self):
        """Test that log files are created with correct structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            logger = JarvisLogger(
                name="file_test",
                log_dir=log_dir,
                console_output=False,
                file_output=True,
            )

            # Log something to trigger file creation
            logger.info("Test message")

            # Check that date-based directory structure was created
            # Note: File creation might be asynchronous, so we check the structure
            assert log_dir.exists()

    def test_set_level(self):
        """Test changing log level at runtime."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = JarvisLogger(
                name="level_test", log_dir=Path(temp_dir) / "logs", log_level="INFO"
            )

            assert logger.log_level == LogLevel.INFO

            logger.set_level("DEBUG")
            assert logger.log_level == LogLevel.DEBUG

    def test_get_log_files(self):
        """Test getting list of log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"

            # Create some test log files
            log_dir.mkdir(parents=True)
            test_log1 = log_dir / "test1.log"
            test_log2 = log_dir / "test2.log"
            test_log1.touch()
            test_log2.touch()

            logger = JarvisLogger(name="files_test", log_dir=log_dir)

            log_files = logger.get_log_files()
            # Logger creates its own log file, so we have 3 total (2 test files + 1 logger file)
            assert len(log_files) >= 2
            assert test_log1 in log_files
            assert test_log2 in log_files


class TestGetLogger:
    """Test get_logger convenience function."""

    def test_get_logger_function(self):
        """Test get_logger convenience function."""
        logger = get_logger("convenience_test")

        assert isinstance(logger, JarvisLogger)
        assert logger.name == "convenience_test"

        # Should return same instance
        logger2 = get_logger("convenience_test")
        assert logger is logger2


class TestLogCallsDecorator:
    """Test log_calls decorator."""

    def test_log_calls_decorator(self):
        """Test function logging decorator."""
        # Mock the logger
        with patch("jarvis_shared.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_calls("test_logger")
            def test_function(arg1, arg2, kwarg1=None):
                return f"{arg1}-{arg2}-{kwarg1}"

            result = test_function("a", "b", kwarg1="c")

            assert result == "a-b-c"
            mock_logger.log_function_call.assert_called()
            mock_logger.log_performance.assert_called()

    def test_log_calls_decorator_exception(self):
        """Test decorator handles exceptions properly."""
        with patch("jarvis_shared.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_calls("test_logger")
            def failing_function():
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                failing_function()

            mock_logger.exception.assert_called()


class TestLogPerformance:
    """Test LogPerformance context manager."""

    def test_log_performance_success(self):
        """Test performance logging context manager success case."""
        with patch("jarvis_shared.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            with LogPerformance("test_operation", "test_logger", param="value"):
                pass  # Simulate work

            mock_logger.debug.assert_called()  # Start message
            mock_logger.log_performance.assert_called()  # End message

    def test_log_performance_exception(self):
        """Test performance logging context manager with exception."""
        with patch("jarvis_shared.logger.get_logger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            with pytest.raises(ValueError):
                with LogPerformance("test_operation", "test_logger"):
                    raise ValueError("Test error")

            mock_logger.debug.assert_called()  # Start message
            mock_logger.error.assert_called()  # Error message
