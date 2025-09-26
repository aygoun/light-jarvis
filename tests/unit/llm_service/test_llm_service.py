"""Tests for LLM Service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from jarvis_shared.models import LLMResponse
from jarvis_llm.llm_service import LLMService


class TestLLMService:
    """Test LLMService class."""

    @pytest.fixture
    def llm_service(self, mock_config):
        """Create LLM service with mocked dependencies."""
        with (
            patch("jarvis_llm.llm_service.OllamaClient"),
            patch("jarvis_llm.llm_service.get_logger") as mock_get_logger,
        ):

            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            service = LLMService(mock_config.ollama)
            service.ollama_client = AsyncMock()
            service.logger = mock_logger

            return service

    @pytest.mark.asyncio
    async def test_chat_with_ollama(self, llm_service, sample_messages):
        """Test chat with Ollama provider."""
        expected_response = LLMResponse(
            content="Hello! How can I help?", model="mistral:7b"
        )

        llm_service.ollama_client.chat = AsyncMock(return_value=expected_response)

        response = await llm_service.chat(sample_messages)

        assert response == expected_response
        llm_service.ollama_client.chat.assert_called_once_with(sample_messages, None)

    @pytest.mark.asyncio
    async def test_chat_with_tools(self, llm_service, sample_messages):
        """Test chat with tools provided."""
        tools = [{"name": "test_tool", "description": "A test tool"}]
        expected_response = LLMResponse(
            content="I'll use the tool.", model="mistral:7b"
        )

        llm_service.ollama_client.chat = AsyncMock(return_value=expected_response)

        response = await llm_service.chat(sample_messages, tools, temperature=0.5)

        assert response == expected_response
        llm_service.ollama_client.chat.assert_called_once_with(
            sample_messages, tools, temperature=0.5
        )

    @pytest.mark.asyncio
    async def test_chat_stream_with_ollama(self, llm_service, sample_messages):
        """Test streaming chat with Ollama provider."""

        async def mock_stream():
            tokens = ["Hello", " there", "!"]
            for token in tokens:
                yield token

        llm_service.ollama_client.chat_stream = AsyncMock(return_value=mock_stream())

        result_tokens = []
        async for token in llm_service.chat_stream(sample_messages):
            result_tokens.append(token)

        assert result_tokens == ["Hello", " there", "!"]
        llm_service.ollama_client.chat_stream.assert_called_once_with(
            sample_messages, None
        )

    @pytest.mark.asyncio
    async def test_chat_stream_with_tools(self, llm_service, sample_messages):
        """Test streaming chat with tools."""
        tools = [{"name": "test_tool"}]

        async def mock_stream():
            tokens = ["Using", " tool", "..."]
            for token in tokens:
                yield token

        llm_service.ollama_client.chat_stream = AsyncMock(return_value=mock_stream())

        result_tokens = []
        async for token in llm_service.chat_stream(
            sample_messages, tools, max_tokens=100
        ):
            result_tokens.append(token)

        assert result_tokens == ["Using", " tool", "..."]
        llm_service.ollama_client.chat_stream.assert_called_once_with(
            sample_messages, tools, max_tokens=100
        )

    def test_set_provider_valid(self, llm_service):
        """Test setting valid provider."""
        assert llm_service.active_provider == "ollama"

        # Currently only ollama is supported
        llm_service.set_provider("ollama")
        assert llm_service.active_provider == "ollama"
        llm_service.logger.info.assert_called_with(
            "🔄 Switched to LLM provider: ollama"
        )

    def test_set_provider_invalid(self, llm_service):
        """Test setting invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            llm_service.set_provider("invalid")

    def test_get_available_models(self, llm_service):
        """Test getting available models."""
        expected_models = ["mistral:7b", "llama3.1:8b"]
        llm_service.ollama_client.list_models = Mock(return_value=expected_models)

        models = llm_service.get_available_models()

        assert models == expected_models
        llm_service.ollama_client.list_models.assert_called_once()

    def test_get_available_models_unsupported_provider(self, llm_service):
        """Test getting models with unsupported provider."""
        llm_service.active_provider = "unsupported"

        models = llm_service.get_available_models()

        assert models == []

    def test_pull_model(self, llm_service):
        """Test pulling a model."""
        llm_service.ollama_client.pull_model = Mock(return_value=True)

        result = llm_service.pull_model("new_model:7b")

        assert result is True
        llm_service.ollama_client.pull_model.assert_called_once_with("new_model:7b")

    def test_pull_model_unsupported_provider(self, llm_service):
        """Test pulling model with unsupported provider."""
        llm_service.active_provider = "unsupported"

        result = llm_service.pull_model("model:7b")

        assert result is False

    @pytest.mark.asyncio
    async def test_chat_unsupported_provider(self, llm_service, sample_messages):
        """Test chat with unsupported provider."""
        llm_service.active_provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported LLM provider: unsupported"):
            await llm_service.chat(sample_messages)

    @pytest.mark.asyncio
    async def test_chat_stream_unsupported_provider(self, llm_service, sample_messages):
        """Test streaming chat with unsupported provider."""
        llm_service.active_provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported LLM provider: unsupported"):
            async for token in llm_service.chat_stream(sample_messages):
                pass

    def test_default_provider(self, llm_service):
        """Test that default provider is ollama."""
        assert llm_service.active_provider == "ollama"

    def test_logger_initialization(self, llm_service):
        """Test that logger is properly initialized."""
        assert llm_service.logger is not None

    @pytest.mark.asyncio
    async def test_chat_kwargs_passed_through(self, llm_service, sample_messages):
        """Test that kwargs are passed through to underlying client."""
        llm_service.ollama_client.chat = AsyncMock(
            return_value=LLMResponse(content="Response", model="mistral:7b")
        )

        await llm_service.chat(
            sample_messages,
            tools=None,
            temperature=0.7,
            max_tokens=150,
            custom_param="value",
        )

        llm_service.ollama_client.chat.assert_called_once_with(
            sample_messages, None, temperature=0.7, max_tokens=150, custom_param="value"
        )

    @pytest.mark.asyncio
    async def test_chat_stream_kwargs_passed_through(
        self, llm_service, sample_messages
    ):
        """Test that kwargs are passed through in streaming mode."""

        async def mock_stream():
            yield "token"

        llm_service.ollama_client.chat_stream = AsyncMock(return_value=mock_stream())

        async for token in llm_service.chat_stream(
            sample_messages, tools=None, temperature=0.8, stream_param="test"
        ):
            pass

        llm_service.ollama_client.chat_stream.assert_called_once_with(
            sample_messages, None, temperature=0.8, stream_param="test"
        )
