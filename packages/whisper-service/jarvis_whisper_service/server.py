"""Whisper Service Server - dedicated STT/TTS functionality."""

from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response

from jarvis_shared.config import WhisperConfig, TTSConfig
from jarvis_shared.logger import get_logger

from .stt_service import STTService
from .tts_service import TTSService


def sanitize_header_text(text: str, max_length: int = 100) -> str:
    """Sanitize text for use in HTTP headers."""
    if not text:
        return "TTS Audio"

    # Remove or replace problematic characters
    sanitized = (
        text.replace("\r", "")
        .replace("\n", " ")
        .replace("\t", " ")
        .replace('"', "'")
        .replace("'", "'")
        .replace("`", "'")
        .replace("\\", "/")
        .replace("\x00", "")  # Remove null bytes
        .replace("\x01", "")  # Remove control characters
        .replace("\x02", "")
        .replace("\x03", "")
        .replace("\x04", "")
        .replace("\x05", "")
        .replace("\x06", "")
        .replace("\x07", "")
        .replace("\x08", "")
        .replace("\x0b", "")
        .replace("\x0c", "")
        .replace("\x0e", "")
        .replace("\x0f", "")
        .strip()
    )

    # Limit length and ensure it's not empty
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip()

    # If empty after sanitization, return a safe default
    return sanitized if sanitized else "TTS Audio"


class WhisperServiceServer:
    """Whisper Service Server for STT/TTS functionality."""

    def __init__(self, whisper_config: WhisperConfig, tts_config: TTSConfig):
        self.whisper_config = whisper_config
        self.tts_config = tts_config
        self.logger = get_logger("jarvis.whisper.service")

        self.app = FastAPI(
            title="Jarvis Whisper Service",
            version="0.1.0",
            description="Dedicated STT/TTS service using Whisper.cpp and Edge-TTS",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Initialize services
        self.stt_service: Optional[STTService] = None
        self.tts_service: Optional[TTSService] = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check() -> Dict[str, Any]:
            """Health check endpoint."""
            stt_health = (
                self.stt_service.get_health_status()
                if self.stt_service
                else {"status": "uninitialized"}
            )
            tts_health = (
                self.tts_service.get_health_status()
                if self.tts_service
                else {"status": "uninitialized"}
            )

            return {
                "status": "healthy",
                "service": "whisper-service",
                "stt": stt_health,
                "tts": tts_health,
            }

        # STT endpoints
        @self.app.post("/stt/transcribe")
        async def transcribe_audio(
            file: UploadFile = File(...),
            language: Optional[str] = Form(None),
            temperature: Optional[float] = Form(None),
        ) -> JSONResponse:
            """Transcribe audio file using Whisper."""
            if not self.stt_service:
                raise HTTPException(
                    status_code=503, detail="STT service not initialized"
                )

            try:
                result = await self.stt_service.transcribe_upload(
                    file=file,
                    language=language,
                    temperature=temperature,
                )
                return JSONResponse(content=result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/stt/transcribe-raw")
        async def transcribe_raw_audio(
            audio_data: bytes = File(...),
            sample_rate: int = Form(16000),
            language: Optional[str] = Form(None),
            temperature: Optional[float] = Form(None),
        ) -> JSONResponse:
            """Transcribe raw audio data using Whisper."""
            if not self.stt_service:
                raise HTTPException(
                    status_code=503, detail="STT service not initialized"
                )

            try:
                result = await self.stt_service.transcribe_audio_data(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    language=language,
                    temperature=temperature,
                )
                return JSONResponse(content=result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/stt/health")
        async def stt_health() -> JSONResponse:
            """Get STT service health status."""
            if not self.stt_service:
                return JSONResponse(
                    content={"status": "unhealthy", "error": "Service not initialized"},
                    status_code=503,
                )
            return JSONResponse(content=self.stt_service.get_health_status())

        @self.app.post("/stt/settings")
        async def update_stt_settings(
            language: Optional[str] = Form(None),
            temperature: Optional[float] = Form(None),
            max_len: Optional[int] = Form(None),
        ) -> JSONResponse:
            """Update STT service settings."""
            if not self.stt_service:
                raise HTTPException(
                    status_code=503, detail="STT service not initialized"
                )

            try:
                result = self.stt_service.update_settings(
                    language=language,
                    temperature=temperature,
                    max_len=max_len,
                )
                return JSONResponse(content=result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # TTS endpoints
        @self.app.post("/tts/speak")
        async def speak_text(text: str = Form(...)):
            """Convert text to speech using config settings."""
            if not self.tts_service:
                raise HTTPException(
                    status_code=503, detail="TTS service not initialized"
                )

            try:
                self.logger.info(f"TTS speak_text called with text: {text[:50]}...")
                result = await self.tts_service.speak_text(text=text)
                self.logger.info(
                    f"TTS result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}"
                )

                if result.get("success") and "audio_data" in result:
                    # Decode base64 audio data
                    import base64

                    audio_data = base64.b64decode(result["audio_data"])

                    # Sanitize text for header
                    text = result.get("text", "")
                    sanitized_text = sanitize_header_text(text)

                    return Response(
                        content=audio_data,
                        media_type="audio/mpeg",
                        headers={
                            "Content-Disposition": "attachment; filename=speech.mp3",
                            "X-Text": sanitized_text,
                            "X-Voice": result.get("voice", ""),
                        },
                    )
                else:
                    # Return error as JSON
                    return JSONResponse(content=result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tts/save")
        async def save_audio(text: str = Form(...)) -> JSONResponse:
            """Convert text to speech and return audio file using config settings."""
            if not self.tts_service:
                raise HTTPException(
                    status_code=503, detail="TTS service not initialized"
                )

            try:
                result = await self.tts_service.save_audio(text=text)

                if result["success"] and "file_path" in result:
                    return FileResponse(
                        path=result["file_path"],
                        media_type="audio/mpeg",
                        filename="speech.mp3",
                    )
                else:
                    return JSONResponse(content=result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/tts/voices")
        async def get_voices() -> JSONResponse:
            """Get available TTS voices."""
            if not self.tts_service:
                raise HTTPException(
                    status_code=503, detail="TTS service not initialized"
                )

            try:
                voices = await self.tts_service.get_available_voices()
                return JSONResponse(content={"voices": voices})
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tts/cleanup")
        async def cleanup_audio_files(max_age_hours: int = 24) -> JSONResponse:
            """Clean up old audio files."""
            if not self.tts_service:
                raise HTTPException(
                    status_code=503, detail="TTS service not initialized"
                )

            try:
                result = self.tts_service.cleanup_old_audio_files(max_age_hours)
                return JSONResponse(content=result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/tts/stats")
        async def get_audio_stats() -> JSONResponse:
            """Get audio storage statistics."""
            if not self.tts_service:
                raise HTTPException(
                    status_code=503, detail="TTS service not initialized"
                )

            try:
                result = self.tts_service.get_audio_stats()
                return JSONResponse(content=result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/tts/health")
        async def tts_health() -> JSONResponse:
            """Get TTS service health status."""
            if not self.tts_service:
                return JSONResponse(
                    content={"status": "unhealthy", "error": "Service not initialized"},
                    status_code=503,
                )
            return JSONResponse(content=self.tts_service.get_health_status())

    async def initialize_services(self) -> None:
        """Initialize STT and TTS services."""
        try:
            # Initialize STT service
            self.logger.info("Initializing STT service...")
            self.stt_service = STTService(self.whisper_config)
            self.logger.info("STT service initialized successfully")

            # Initialize TTS service
            self.logger.info("Initializing TTS service...")
            self.tts_service = TTSService(self.tts_config)
            self.logger.info("TTS service initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize services: {e}", exc_info=True)
            raise

    async def start_server(self, host: str = "localhost", port: int = 3001) -> None:
        """Start the Whisper Service server."""
        import uvicorn

        self.logger.info("Starting Whisper Service Server")

        # Initialize services
        await self.initialize_services()

        # Start server
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
