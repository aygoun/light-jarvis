"""LLM service orchestrator for different LLM providers."""

from typing import AsyncGenerator, Dict, Any, List, Optional
from jarvis_shared.config import OllamaConfig
from jarvis_shared.models import Message, LLMResponse
from jarvis_shared.logger import get_logger

from .ollama_client import OllamaClient


class LLMService:
    """Service for managing different LLM providers."""

    def __init__(self, config: OllamaConfig):
        self.config = config
        self.logger = get_logger("jarvis.llm.service")

        # Initialize providers
        self.ollama_client = OllamaClient(config)
        self.active_provider = "ollama"  # Default to Ollama

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send chat request to active LLM provider."""
        if self.active_provider == "ollama":
            return await self.ollama_client.chat(messages, tools, **kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.active_provider}")

    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from active LLM provider."""
        if self.active_provider == "ollama":
            async for token in self.ollama_client.chat_stream(
                messages, tools, **kwargs
            ):
                yield token
        else:
            raise ValueError(f"Unsupported LLM provider: {self.active_provider}")

    def set_provider(self, provider: str):
        """Switch LLM provider."""
        if provider not in ["ollama"]:
            raise ValueError(f"Unsupported provider: {provider}")

        self.active_provider = provider
        self.logger.info(f"🔄 Switched to LLM provider: {provider}")

    def get_available_models(self) -> List[str]:
        """Get available models from active provider."""
        if self.active_provider == "ollama":
            return self.ollama_client.list_models()
        else:
            return []

    def pull_model(self, model_name: str) -> bool:
        """Pull a model for the active provider."""
        if self.active_provider == "ollama":
            return self.ollama_client.pull_model(model_name)
        else:
            return False
