"""Whisper Service Client for communicating with the Whisper Service server."""

import aiohttp
from typing import Dict, Any, List, Optional
from jarvis_shared.logger import get_logger


class WhisperServiceClient:
    """Client for communicating with the Whisper Service server."""

    def __init__(self, base_url: str = "http://localhost:3001"):
        self.base_url = base_url
        self.logger = get_logger("jarvis.whisper.client")
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> None:
        """Connect to the Whisper Service server."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        self.logger.info(f"Connected to Whisper Service at {self.base_url}")

    async def disconnect(self) -> None:
        """Disconnect from the Whisper Service server."""
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("Disconnected from Whisper Service")

    async def health_check(self) -> Dict[str, Any]:
        """Check server health."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.get(f"{self.base_url}/health") as response:
            response.raise_for_status()
            return await response.json()

    # STT methods
    async def transcribe_audio(
        self,
        audio_data: bytes,
        filename: str = "audio.webm",
        language: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio data."""
        if not self.session:
            raise RuntimeError("Client not connected")

        # Prepare form data
        data = aiohttp.FormData()
        data.add_field("file", audio_data, filename=filename, content_type="audio/webm")

        if language:
            data.add_field("language", language)
        if temperature is not None:
            data.add_field("temperature", str(temperature))

        async with self.session.post(
            f"{self.base_url}/stt/transcribe", data=data
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def transcribe_raw_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Transcribe raw audio data."""
        if not self.session:
            raise RuntimeError("Client not connected")

        # Prepare form data
        data = aiohttp.FormData()
        data.add_field(
            "audio_data", audio_data, content_type="application/octet-stream"
        )
        data.add_field("sample_rate", str(sample_rate))

        if language:
            data.add_field("language", language)
        if temperature is not None:
            data.add_field("temperature", str(temperature))

        async with self.session.post(
            f"{self.base_url}/stt/transcribe-raw", data=data
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_stt_health(self) -> Dict[str, Any]:
        """Get STT service health."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.get(f"{self.base_url}/stt/health") as response:
            response.raise_for_status()
            return await response.json()

    async def update_stt_settings(
        self,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
        max_len: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update STT service settings."""
        if not self.session:
            raise RuntimeError("Client not connected")

        data = aiohttp.FormData()
        if language:
            data.add_field("language", language)
        if temperature is not None:
            data.add_field("temperature", str(temperature))
        if max_len is not None:
            data.add_field("max_len", str(max_len))

        async with self.session.post(
            f"{self.base_url}/stt/settings", data=data
        ) as response:
            response.raise_for_status()
            return await response.json()

    # TTS methods
    async def speak_text(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Convert text to speech."""
        if not self.session:
            raise RuntimeError("Client not connected")

        data = aiohttp.FormData()
        data.add_field("text", text)

        if voice:
            data.add_field("voice", voice)
        if rate is not None:
            data.add_field("rate", str(rate))
        if volume is not None:
            data.add_field("volume", str(volume))

        async with self.session.post(
            f"{self.base_url}/tts/speak", data=data
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def speak_text_raw(self, text: str) -> bytes:
        """Convert text to speech and return raw audio data using config settings."""
        if not self.session:
            raise RuntimeError("Client not connected")

        data = aiohttp.FormData()
        data.add_field("text", text)

        async with self.session.post(
            f"{self.base_url}/tts/speak", data=data
        ) as response:
            response.raise_for_status()
            return await response.read()

    async def save_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
    ) -> bytes:
        """Convert text to speech and return audio data."""
        if not self.session:
            raise RuntimeError("Client not connected")

        data = aiohttp.FormData()
        data.add_field("text", text)

        if voice:
            data.add_field("voice", voice)
        if rate is not None:
            data.add_field("rate", str(rate))
        if volume is not None:
            data.add_field("volume", str(volume))

        async with self.session.post(
            f"{self.base_url}/tts/save", data=data
        ) as response:
            response.raise_for_status()
            return await response.read()

    async def get_voices(self) -> List[Dict[str, Any]]:
        """Get available TTS voices."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.get(f"{self.base_url}/tts/voices") as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("voices", [])

    async def get_tts_health(self) -> Dict[str, Any]:
        """Get TTS service health."""
        if not self.session:
            raise RuntimeError("Client not connected")

        async with self.session.get(f"{self.base_url}/tts/health") as response:
            response.raise_for_status()
            return await response.json()

    async def update_tts_settings(
        self,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Update TTS service settings."""
        if not self.session:
            raise RuntimeError("Client not connected")

        data = aiohttp.FormData()
        if voice:
            data.add_field("voice", voice)
        if rate is not None:
            data.add_field("rate", str(rate))
        if volume is not None:
            data.add_field("volume", str(volume))

        async with self.session.post(
            f"{self.base_url}/tts/settings", data=data
        ) as response:
            response.raise_for_status()
            return await response.json()
