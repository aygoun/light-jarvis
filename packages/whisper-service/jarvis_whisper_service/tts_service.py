"""Text-to-Speech service using Edge-TTS."""

import hashlib
from pathlib import Path
from typing import Dict, Any, List

from jarvis_shared.config import TTSConfig
from jarvis_shared.logger import get_logger
from .edge_tts_client import EdgeTTSClient


class TTSService:
    """Text-to-Speech service using Edge-TTS."""

    def __init__(self, config: TTSConfig):
        self.config = config
        self.logger = get_logger("jarvis.whisper.tts")
        self.client = EdgeTTSClient(
            voice=config.voice,
            rate=config.rate,
            volume=config.volume,
        )

        # Create audio storage directory
        self.audio_dir = Path("audio")
        self.audio_dir.mkdir(exist_ok=True)

    async def speak_text(self, text: str) -> Dict[str, Any]:
        """Convert text to speech using config settings."""
        self.logger.info(f"Processing TTS request: {text[:50]}...")

        try:
            result = await self.client.speak_text(text)

            # Convert audio data to base64 for JSON serialization
            if result.get("success") and "audio_data" in result:
                import base64

                audio_data = result["audio_data"]
                result["audio_data"] = base64.b64encode(audio_data).decode("utf-8")
                result["audio_url"] = f"data:audio/mpeg;base64,{result['audio_data']}"

            return result

        except Exception as e:
            self.logger.error(f"TTS speak_text failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def save_audio(self, text: str) -> Dict[str, Any]:
        """Convert text to speech and save to local audio directory using config settings."""
        self.logger.info(f"Saving TTS audio: {text[:50]}...")

        # Create hash-based filename for caching
        text_hash = hashlib.md5(
            f"{text}_{self.client.voice}_{self.client.rate}_{self.client.volume}".encode()
        ).hexdigest()
        filename = f"tts_{text_hash}.mp3"
        output_path = self.audio_dir / filename

        # Check if file already exists (cache hit)
        if output_path.exists():
            self.logger.info(f"Using cached audio file: {filename}")
            return {
                "success": True,
                "file_path": str(output_path),
                "cached": True,
                "text": text,
                "voice": self.client.voice,
                "rate": self.client.rate,
                "volume": self.client.volume,
            }

        try:
            result = await self.client.save_audio(text, str(output_path))

            if result["success"]:
                result["file_path"] = str(output_path)
                result["cached"] = False
                result["text"] = text
                result["voice"] = self.client.voice
                result["rate"] = self.client.rate
                result["volume"] = self.client.volume

            return result

        except Exception as e:
            self.logger.error(f"TTS save_audio failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status."""
        try:
            voices = self.client.get_available_voices_sync()
            return {
                "status": "healthy",
                "voice": self.client.voice,
                "rate": self.client.rate,
                "volume": self.client.volume,
                "available_voices": len(voices),
                "voices": voices,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        try:
            return await self.client.get_available_voices()
        except Exception as e:
            self.logger.error(f"Failed to get available voices: {e}")
            # Return a fallback voice list
            return [
                {
                    "name": "Default Voice",
                    "short_name": "en-US-AriaNeural",
                    "gender": "Female",
                    "locale": "en-US",
                    "friendly_name": "Aria (Neural)",
                }
            ]

    def cleanup_old_audio_files(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """Clean up old audio files to prevent disk space issues."""
        try:
            import time

            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            deleted_count = 0
            total_size = 0

            for file_path in self.audio_dir.glob("tts_*.mp3"):
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    total_size += file_size
                    self.logger.info(f"Deleted old audio file: {file_path.name}")

            return {
                "success": True,
                "deleted_files": deleted_count,
                "freed_space_bytes": total_size,
                "max_age_hours": max_age_hours,
            }
        except Exception as e:
            self.logger.error(f"Failed to cleanup audio files: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_audio_stats(self) -> Dict[str, Any]:
        """Get statistics about stored audio files."""
        try:
            audio_files = list(self.audio_dir.glob("tts_*.mp3"))
            total_files = len(audio_files)
            total_size = sum(f.stat().st_size for f in audio_files)

            # Get file age distribution
            import time

            current_time = time.time()
            age_ranges = {
                "0-1_hours": 0,
                "1-6_hours": 0,
                "6-24_hours": 0,
                "1-7_days": 0,
                "older_than_7_days": 0,
            }

            for file_path in audio_files:
                age_hours = (current_time - file_path.stat().st_mtime) / 3600
                if age_hours < 1:
                    age_ranges["0-1_hours"] += 1
                elif age_hours < 6:
                    age_ranges["1-6_hours"] += 1
                elif age_hours < 24:
                    age_ranges["6-24_hours"] += 1
                elif age_hours < 168:  # 7 days
                    age_ranges["1-7_days"] += 1
                else:
                    age_ranges["older_than_7_days"] += 1

            return {
                "success": True,
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "age_distribution": age_ranges,
                "audio_directory": str(self.audio_dir),
            }
        except Exception as e:
            self.logger.error(f"Failed to get audio stats: {e}")
            return {
                "success": False,
                "error": str(e),
            }
