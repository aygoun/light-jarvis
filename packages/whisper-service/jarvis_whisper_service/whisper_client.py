"""Whisper client for speech-to-text functionality."""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from jarvis_shared.logger import get_logger


class WhisperClient:
    """Whisper client for speech-to-text functionality."""

    def __init__(
        self,
        model_path: str,
        whisper_cpp_path: str = "whisper.cpp/main",
        language: str = "en",
        temperature: float = 0.0,
        max_len: int = 448,
    ):
        self.model_path = Path(model_path)
        self.whisper_cpp_path = Path(whisper_cpp_path)
        self.language = language
        self.temperature = temperature
        self.max_len = max_len
        self.logger = get_logger("jarvis.whisper.client")

    def transcribe_file(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio file using Whisper.cpp."""
        try:
            self.logger.info(f"Transcribing audio file: {audio_path}")

            # Check if model exists
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model file not found: {self.model_path}")

            # Check if whisper.cpp exists
            if not self.whisper_cpp_path.exists():
                raise FileNotFoundError(
                    f"Whisper.cpp not found: {self.whisper_cpp_path}"
                )

            # Prepare command
            cmd = [
                str(self.whisper_cpp_path),
                "-m",
                str(self.model_path),
                "-f",
                audio_path,
                "-l",
                self.language,
                "-t",
                str(self.temperature),
                "--print-progress",
                "--print-colors",
            ]

            self.logger.debug(f"Running command: {' '.join(cmd)}")

            # Run whisper.cpp
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                self.logger.error(f"Whisper.cpp failed: {result.stderr}")
                raise RuntimeError(f"Whisper.cpp failed: {result.stderr}")

            # Parse output
            output_lines = result.stdout.strip().split("\n")

            # Find the transcription (usually the last line)
            transcription = ""
            for line in reversed(output_lines):
                if line.strip() and not line.startswith("whisper_model_load"):
                    transcription = line.strip()
                    break

            if not transcription:
                transcription = ""

            self.logger.info(f"Transcription completed: {transcription[:100]}...")

            return {
                "success": True,
                "text": transcription,
                "language": self.language,
                "temperature": self.temperature,
                "model": str(self.model_path),
            }

        except subprocess.TimeoutExpired:
            self.logger.error("Whisper.cpp timed out")
            return {
                "success": False,
                "error": "Transcription timed out",
            }
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def transcribe_audio_data(
        self, audio_data: np.ndarray, sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """Transcribe raw audio data using Whisper.cpp."""
        try:
            self.logger.info("Transcribing raw audio data")

            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                wav_path = tmp_file.name

            # Save audio data as WAV file
            import soundfile as sf

            sf.write(wav_path, audio_data, sample_rate)

            try:
                # Transcribe the temporary file
                result = self.transcribe_file(wav_path)
                return result
            finally:
                # Clean up temporary file
                Path(wav_path).unlink(missing_ok=True)

        except Exception as e:
            self.logger.error(f"Raw audio transcription failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        try:
            models_dir = self.model_path.parent
            if not models_dir.exists():
                return []

            # Look for .bin files in the models directory
            model_files = []
            for file_path in models_dir.glob("*.bin"):
                model_files.append(file_path.name)

            return model_files

        except Exception as e:
            self.logger.error(f"Failed to get available models: {e}")
            return []

    def update_settings(
        self,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
        max_len: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update client settings."""
        if language is not None:
            self.language = language
        if temperature is not None:
            self.temperature = temperature
        if max_len is not None:
            self.max_len = max_len

        return {
            "language": self.language,
            "temperature": self.temperature,
            "max_len": self.max_len,
        }
