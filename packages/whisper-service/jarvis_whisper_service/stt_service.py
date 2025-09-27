"""Speech-to-Text service using Whisper.cpp."""

import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import aiofiles
from fastapi import UploadFile, HTTPException
import numpy as np
import soundfile as sf
import librosa
import subprocess

from jarvis_shared.config import WhisperConfig
from jarvis_shared.logger import get_logger
from .whisper_client import WhisperClient


class STTService:
    """Speech-to-Text service using Whisper.cpp."""

    def __init__(self, config: WhisperConfig):
        self.config = config
        self.logger = get_logger("jarvis.whisper.stt")
        self.client = WhisperClient(
            model_path=config.model_path,
            whisper_cpp_path=config.whisper_cpp_path,
            language=config.language,
            temperature=config.temperature,
            max_len=config.max_len,
        )

    async def transcribe_upload(
        self,
        file: UploadFile,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Transcribe uploaded audio file."""
        self.logger.info(f"Processing audio upload: {file.filename}")

        # Validate file type
        if not file.content_type or not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Read file content
        content = await file.read()
        self.logger.debug(f"Audio file size: {len(content)} bytes")

        # Create temporary file with original extension
        original_ext = Path(file.filename).suffix if file.filename else ".webm"
        with tempfile.NamedTemporaryFile(suffix=original_ext, delete=False) as tmp_file:
            tmp_path = tmp_file.name

        # Write content to temporary file
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(content)

        try:
            # Convert audio to WAV format for Whisper
            wav_path = await self._convert_to_wav(tmp_path)
            self.logger.debug(f"Converted audio to WAV: {wav_path}")

            # Override settings if provided
            original_language = self.client.language
            original_temperature = self.client.temperature

            if language:
                self.client.language = language
            if temperature is not None:
                self.client.temperature = temperature

            # Transcribe
            result = self.client.transcribe_file(wav_path)

            # Restore original settings
            self.client.language = original_language
            self.client.temperature = original_temperature

            return result

        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Transcription failed: {str(e)}"
            )

        finally:
            # Clean up temporary files
            Path(tmp_path).unlink(missing_ok=True)
            if "wav_path" in locals():
                Path(wav_path).unlink(missing_ok=True)

    async def transcribe_audio_data(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Transcribe raw audio data."""
        self.logger.info("Processing raw audio data")

        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)

            # Convert to float32 and normalize
            audio_array = audio_array.astype(np.float32) / 32767.0

            # Override settings if provided
            original_language = self.client.language
            original_temperature = self.client.temperature

            if language:
                self.client.language = language
            if temperature is not None:
                self.client.temperature = temperature

            # Transcribe
            result = self.client.transcribe_audio_data(audio_array, sample_rate)

            # Restore original settings
            self.client.language = original_language
            self.client.temperature = original_temperature

            return result

        except Exception as e:
            self.logger.error(f"Raw audio transcription failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Transcription failed: {str(e)}"
            )

    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status."""
        try:
            models = self.client.get_available_models()
            return {
                "status": "healthy",
                "model_path": str(self.client.model_path),
                "language": self.client.language,
                "temperature": self.client.temperature,
                "available_models": len(models),
                "models": models,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def update_settings(
        self,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
        max_len: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update service settings."""
        if language is not None:
            self.client.language = language
        if temperature is not None:
            self.client.temperature = temperature
        if max_len is not None:
            self.client.max_len = max_len

        return {
            "language": self.client.language,
            "temperature": self.client.temperature,
            "max_len": self.client.max_len,
        }

    async def _convert_to_wav(self, input_path: str) -> str:
        """Convert audio file to WAV format using ffmpeg."""
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                wav_path = tmp_file.name

            # Use ffmpeg to convert to WAV format
            cmd = [
                "/opt/homebrew/bin/ffmpeg",
                "-i",
                input_path,
                "-ar",
                "16000",  # Sample rate 16kHz
                "-ac",
                "1",  # Mono
                "-y",  # Overwrite output file
                "-c:a",
                "pcm_s16le",
                wav_path,
            ]

            self.logger.debug(f"Running ffmpeg command: {' '.join(cmd)}")

            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                self.logger.error(f"ffmpeg failed: {result.stderr}")
                raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

            self.logger.debug(f"Converted to WAV: {wav_path}")

            # Verify the converted file exists and has content
            if not Path(wav_path).exists() or Path(wav_path).stat().st_size == 0:
                raise RuntimeError("Converted WAV file is empty or doesn't exist")

            return wav_path

        except subprocess.TimeoutExpired:
            self.logger.error("ffmpeg conversion timed out")
            raise RuntimeError("Audio conversion timed out")
        except FileNotFoundError:
            self.logger.warning("ffmpeg not found, trying librosa fallback")
            return await self._convert_to_wav_librosa(input_path)
        except Exception as e:
            self.logger.error(f"Audio conversion failed: {e}")
            raise RuntimeError(f"Failed to convert audio to WAV: {e}")

    async def _convert_to_wav_librosa(self, input_path: str) -> str:
        """Convert audio file to WAV format using librosa (fallback)."""
        try:
            self.logger.debug(f"Converting with librosa: {input_path}")

            # Load audio with librosa
            audio_data, sample_rate = librosa.load(input_path, sr=16000, mono=True)

            self.logger.debug(
                f"Loaded audio: {len(audio_data)} samples at {sample_rate}Hz"
            )

            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                wav_path = tmp_file.name

            # Save as WAV file
            sf.write(wav_path, audio_data, sample_rate)
            self.logger.debug(f"Saved WAV file: {wav_path}")

            # Verify the converted file exists and has content
            if not Path(wav_path).exists() or Path(wav_path).stat().st_size == 0:
                raise RuntimeError("Converted WAV file is empty or doesn't exist")

            return wav_path

        except Exception as e:
            self.logger.error(f"librosa conversion failed: {e}")
            raise RuntimeError(f"librosa conversion failed: {e}")
