"""Whisper Service for Jarvis - dedicated STT/TTS functionality."""

from .server import WhisperServiceServer
from .client import WhisperServiceClient

__all__ = ["WhisperServiceServer", "WhisperServiceClient"]
