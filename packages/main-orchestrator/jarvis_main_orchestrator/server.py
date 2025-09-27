"""Main Orchestrator Server - coordinates all services."""

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis_shared.config import JarvisConfig
from jarvis_shared.logger import get_logger

from .assistant import JarvisAssistant


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


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    use_stt: bool = False


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    success: bool
    error: Optional[str] = None


class MainOrchestratorServer:
    """Main Orchestrator Server that coordinates all services."""

    def __init__(self, config: JarvisConfig):
        self.config = config
        self.logger = get_logger("jarvis.main.orchestrator")

        self.app = FastAPI(
            title="Jarvis Main Orchestrator",
            version="0.1.0",
            description="Main orchestrator that coordinates all Jarvis services",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Initialize assistant
        self.assistant: Optional[JarvisAssistant] = None

        # Setup routes
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check() -> Dict[str, Any]:
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "main-orchestrator",
                "assistant_initialized": self.assistant is not None,
            }

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest) -> ChatResponse:
            """Process chat request."""
            try:
                if not self.assistant:
                    raise HTTPException(
                        status_code=503, detail="Assistant not initialized"
                    )

                response = await self.assistant.process_command(request.message)

                return ChatResponse(response=response, success=True)

            except Exception as e:
                self.logger.error(f"Chat processing failed: {e}", exc_info=True)
                return ChatResponse(response="", success=False, error=str(e))

        @self.app.post("/chat/stream")
        async def chat_stream(request: ChatRequest):
            """Process chat request with streaming response."""
            try:
                if not self.assistant:
                    raise HTTPException(
                        status_code=503, detail="Assistant not initialized"
                    )

                async def generate():
                    async for token in self.assistant.process_command_stream(
                        request.message
                    ):
                        yield f"data: {token}\n\n"
                    yield "data: [DONE]\n\n"

                return StreamingResponse(
                    generate(),
                    media_type="text/plain",
                    headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
                )

            except Exception as e:
                self.logger.error(
                    f"Streaming chat processing failed: {e}", exc_info=True
                )
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/stt/transcribe")
        async def transcribe_audio(
            file: UploadFile = File(...),
            language: Optional[str] = Form(None),
            temperature: Optional[float] = Form(None),
        ) -> JSONResponse:
            """Transcribe audio file using Whisper service."""
            try:
                if not self.assistant:
                    raise HTTPException(
                        status_code=503, detail="Assistant not initialized"
                    )

                result = await self.assistant.transcribe_audio(
                    file=file,
                    language=language,
                    temperature=temperature,
                )
                return JSONResponse(content=result)

            except Exception as e:
                self.logger.error(f"Audio transcription failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/tts/speak")
        async def speak_text(text: str = Form(...)):
            """Convert text to speech using TTS service with config settings."""
            try:
                if not self.assistant:
                    raise HTTPException(
                        status_code=503, detail="Assistant not initialized"
                    )

                # Call the whisper service directly to get audio data
                audio_data = await self.assistant.whisper_client.speak_text_raw(
                    text=text
                )

                # Sanitize text for header
                sanitized_text = sanitize_header_text(text)

                return Response(
                    content=audio_data,
                    media_type="audio/mpeg",
                    headers={
                        "Content-Disposition": "attachment; filename=speech.mp3",
                        "X-Text": sanitized_text,
                        "X-Voice": "",
                    },
                )

            except Exception as e:
                self.logger.error(f"TTS failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/services/status")
        async def services_status() -> Dict[str, Any]:
            """Get status of all services."""
            try:
                if not self.assistant:
                    return {
                        "assistant": {"status": "not_initialized"},
                        "mcp_orchestrator": {"status": "unknown"},
                        "whisper_service": {"status": "unknown"},
                        "llm_service": {"status": "unknown"},
                    }

                return await self.assistant.get_services_status()

            except Exception as e:
                self.logger.error(f"Failed to get services status: {e}", exc_info=True)
                return {
                    "error": str(e),
                    "assistant": {"status": "error"},
                    "mcp_orchestrator": {"status": "unknown"},
                    "whisper_service": {"status": "unknown"},
                    "llm_service": {"status": "unknown"},
                }

    async def initialize(self) -> None:
        """Initialize the main orchestrator and all services."""
        try:
            self.logger.info("Initializing Main Orchestrator...")

            # Initialize assistant
            self.assistant = JarvisAssistant(self.config)
            await self.assistant.initialize()

            self.logger.info("Main Orchestrator initialized successfully")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize Main Orchestrator: {e}", exc_info=True
            )
            raise

    async def start_server(self, host: str = "localhost", port: int = 3002) -> None:
        """Start the Main Orchestrator server."""
        import uvicorn

        self.logger.info("Starting Main Orchestrator Server")

        # Initialize services
        await self.initialize()

        # Start server
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
