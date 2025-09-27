"""Edge TTS client for text-to-speech functionality."""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

import edge_tts

from jarvis_shared.logger import get_logger


class EdgeTTSClient:
    """Edge TTS client for text-to-speech functionality."""

    def __init__(
        self,
        voice: Optional[str] = None,
        rate: int = 150,
        volume: float = 0.8,
    ):
        self.voice = voice or "en-US-DavisNeural"
        self.rate = rate
        self.volume = volume
        self.logger = get_logger("jarvis.whisper.edge_tts")

    async def speak_text(self, text: str) -> Dict[str, Any]:
        """Convert text to speech and return audio data."""
        try:
            # Limit text length to prevent very long processing times
            if len(text) > 1000:
                text = text[:1000] + "..."
                self.logger.warning("Text truncated to 1000 characters")

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                output_path = tmp_file.name

            # Generate speech with timeout
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=f"+{self.rate}%" if self.rate > 0 else f"{self.rate}%",
                volume=(
                    f"+{int(self.volume * 100)}%"
                    if self.volume > 0
                    else f"{int(self.volume * 100)}%"
                ),
            )

            # Add timeout to prevent infinite loops
            await asyncio.wait_for(communicate.save(output_path), timeout=60.0)

            # Read the generated audio file
            with open(output_path, "rb") as f:
                audio_data = f.read()

            # Clean up temporary file
            Path(output_path).unlink(missing_ok=True)

            return {
                "success": True,
                "audio_data": audio_data,
                "text": text,
                "voice": self.voice,
                "rate": self.rate,
                "volume": self.volume,
            }

        except asyncio.TimeoutError:
            self.logger.error("TTS generation timed out")
            return {
                "success": False,
                "error": "TTS generation timed out",
            }
        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def save_audio(self, text: str, output_path: str) -> Dict[str, Any]:
        """Convert text to speech and save to file."""
        try:
            # Limit text length to prevent very long processing times
            if len(text) > 1000:
                text = text[:1000] + "..."
                self.logger.warning("Text truncated to 1000 characters")

            # Generate speech
            communicate = edge_tts.Communicate(
                text=text,
                voice=self.voice,
                rate=f"+{self.rate}%" if self.rate > 0 else f"{self.rate}%",
                volume=(
                    f"+{int(self.volume * 100)}%"
                    if self.volume > 0
                    else f"{int(self.volume * 100)}%"
                ),
            )

            # Add timeout to prevent infinite loops
            await asyncio.wait_for(communicate.save(output_path), timeout=60.0)

            return {
                "success": True,
                "file_path": output_path,
                "text": text,
                "voice": self.voice,
                "rate": self.rate,
                "volume": self.volume,
            }

        except asyncio.TimeoutError:
            self.logger.error("TTS save timed out")
            return {
                "success": False,
                "error": "TTS save timed out",
            }
        except Exception as e:
            self.logger.error(f"TTS save failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        try:
            voices = await edge_tts.list_voices()

            # Convert to our format - handle different voice data structures
            voice_list = []
            for voice in voices:
                try:
                    voice_data = {
                        "Name": voice.get("Name", voice.get("name", "")),
                        "ShortName": voice.get(
                            "ShortName", voice.get("short_name", "")
                        ),
                        "Gender": voice.get("Gender", voice.get("gender", "")),
                        "Locale": voice.get("Locale", voice.get("locale", "")),
                        "FriendlyName": voice.get(
                            "FriendlyName", voice.get("friendly_name", "")
                        ),
                    }

                    voice_list.append(
                        {
                            "name": voice_data["Name"],
                            "short_name": voice_data["ShortName"],
                            "gender": voice_data["Gender"],
                            "locale": voice_data["Locale"],
                            "friendly_name": voice_data["FriendlyName"],
                        }
                    )
                except Exception as voice_error:
                    self.logger.warning(
                        f"Skipping voice due to parsing error: {voice_error}"
                    )
                    continue

            return voice_list

        except Exception as e:
            self.logger.error(f"Failed to get voices: {e}")
            return []

    def get_available_voices_sync(self) -> List[Dict[str, Any]]:
        """Get list of available voices (synchronous version)."""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, return empty list to avoid conflicts
                self.logger.warning(
                    "Cannot get voices synchronously while in event loop"
                )
                return []
            except RuntimeError:
                # No event loop running, we can create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.get_available_voices())
                finally:
                    loop.close()
        except Exception as e:
            self.logger.error(f"Failed to get voices (sync): {e}")
            return []

    def update_settings(
        self,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update TTS settings."""
        if voice is not None:
            self.voice = voice
        if rate is not None:
            self.rate = rate
        if volume is not None:
            self.volume = volume

        return {
            "voice": self.voice,
            "rate": self.rate,
            "volume": self.volume,
        }
