"""Ollama LLM client for Jarvis."""

import json
from typing import Any, Dict, List, Optional, AsyncGenerator

import ollama
from jarvis_shared.config import OllamaConfig
from jarvis_shared.models import LLMResponse, Message, ToolCall
from jarvis_shared.logger import get_logger


class OllamaClient:
    """Client for interacting with Ollama LLM."""

    def __init__(self, config: OllamaConfig):
        self.config = config
        self.client = ollama.Client(host=config.host)
        self.logger = get_logger("jarvis.llm")

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        """Send chat request to Ollama."""

        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role.value, "content": msg.content} for msg in messages
        ]

        # Prepare request
        request_data = {
            "model": self.config.model,
            "messages": ollama_messages,
            "options": {"temperature": self.config.temperature, **kwargs},
        }

        # Add tools if provided
        if tools:
            request_data["tools"] = tools

        try:
            response = self.client.chat(
                model=self.config.model,
                messages=ollama_messages,
                tools=tools if tools else None,
                options={"temperature": self.config.temperature, **kwargs},
            )
            return self._parse_response(response)
        except Exception as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    async def chat_stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from Ollama token by token."""

        # Convert messages to Ollama format
        ollama_messages = [
            {"role": msg.role.value, "content": msg.content} for msg in messages
        ]

        # Prepare request
        request_data = {
            "model": self.config.model,
            "messages": ollama_messages,
            "options": {"temperature": self.config.temperature, **kwargs},
            "stream": True,
        }

        # Add tools if provided
        if tools:
            request_data["tools"] = tools

        try:
            self.logger.debug(
                f"🔄 Starting streaming chat with model {self.config.model}"
            )

            # Use Ollama's streaming chat
            stream = self.client.chat(
                model=self.config.model,
                messages=ollama_messages,
                tools=tools if tools else None,
                options={"temperature": self.config.temperature, **kwargs},
                stream=True,
            )

            for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    if content:  # Only yield non-empty content
                        yield content

                # Handle tool calls in streaming (if they come in chunks)
                if chunk.get("done", False):
                    self.logger.debug("✅ Streaming completed")
                    break

        except Exception as e:
            self.logger.error(f"❌ Streaming request failed: {e}")
            raise RuntimeError(f"Ollama streaming request failed: {e}")

    def _parse_response(self, response: Dict[str, Any]) -> LLMResponse:
        """Parse Ollama response into LLMResponse model."""

        content = response.get("message", {}).get("content", "")
        tool_calls = []

        # Parse tool calls if present
        if "tool_calls" in response.get("message", {}):
            for tool_call in response["message"]["tool_calls"]:
                tool_calls.append(
                    ToolCall(
                        id=tool_call.get("id", ""),
                        name=tool_call["function"]["name"],
                        arguments=json.loads(tool_call["function"]["arguments"]),
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            model=response.get("model", self.config.model),
            usage=response.get("usage", {}),
        )

    def list_models(self) -> List[str]:
        """List available models."""
        try:
            models = self.client.list()
            return [model["name"] for model in models["models"]]
        except Exception as e:
            raise RuntimeError(f"Failed to list models: {e}")

    def pull_model(self, model_name: str) -> bool:
        """Pull a model if not available."""
        try:
            self.client.pull(model_name)
            return True
        except Exception as e:
            print(f"Failed to pull model {model_name}: {e}")
            return False
