"""Main Jarvis Assistant that coordinates all services."""

from datetime import datetime
from typing import List, Optional, AsyncGenerator, Dict, Any

from jarvis_shared.config import JarvisConfig
from jarvis_shared.models import Message, MessageRole
from jarvis_shared.logger import get_logger, LogPerformance

from jarvis_llm import LLMService
from jarvis_mcp_orchestrator import MCPOrchestratorClient
from jarvis_whisper_service import WhisperServiceClient


class JarvisAssistant:
    """Main Jarvis assistant that orchestrates all services."""

    def __init__(self, config: JarvisConfig):
        self.config = config
        self.logger = get_logger("jarvis.assistant")

        # Initialize services
        self.llm_service = LLMService(config.ollama)
        self.mcp_client = MCPOrchestratorClient(config.mcp)
        self.whisper_client = WhisperServiceClient("http://localhost:3001")

        # Conversation state
        self.conversation_history: List[Message] = []

        # System prompt
        with open("config/prompt.txt", "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

    async def initialize(self) -> None:
        """Initialize the assistant and connect to all services."""
        with LogPerformance("assistant_initialization", "jarvis.assistant"):
            self.logger.info("🚀 Initializing Jarvis Assistant")

            # Connect to services
            await self.mcp_client.connect()
            await self.whisper_client.connect()

            # Add system message to conversation
            self.conversation_history.append(
                Message(role=MessageRole.SYSTEM, content=self.system_prompt)
            )

            self.logger.info("✅ Jarvis Assistant initialized successfully")

    async def process_command(self, user_input: str) -> str:
        """Process a user command and return response."""
        with LogPerformance(
            "command_processing", "jarvis.assistant", command_length=len(user_input)
        ):
            self.logger.info(
                f"💬 Processing user command: {user_input[:100]}{'...' if len(user_input) > 100 else ''}"
            )

            # Add user message to conversation
            user_message = Message(role=MessageRole.USER, content=user_input)
            self.conversation_history.append(user_message)

            # Get available tools
            tools = await self.mcp_client.list_tools()
            self.logger.debug(f"🔧 Available tools: {[tool['name'] for tool in tools]}")

            # Convert tools to LLM format
            llm_tools = self._convert_tools_for_llm(tools)
            self.logger.debug(
                f"🔧 Converted {len(llm_tools) if llm_tools else 0} tools for LLM"
            )

            # Get LLM response
            start_time = datetime.now()
            llm_response = await self.llm_service.chat(
                messages=self.conversation_history,
                tools=llm_tools if llm_tools else None,
            )
            llm_duration = (datetime.now() - start_time).total_seconds()
            self.logger.log_performance(
                "llm_chat",
                llm_duration,
                model=self.config.ollama.model,
                tool_calls=len(llm_response.tool_calls),
            )

            # Execute any tool calls
            final_content = llm_response.content
            if llm_response.tool_calls:
                self.logger.info(
                    f"🛠️  Executing {len(llm_response.tool_calls)} tool calls"
                )
                tool_results = []
                for tool_call in llm_response.tool_calls:
                    tool_start = datetime.now()
                    result = await self.mcp_client.execute_tool(
                        tool_call.name, tool_call.arguments, tool_call.id
                    )
                    tool_duration = (datetime.now() - tool_start).total_seconds()

                    self.logger.log_tool_execution(
                        tool_call.name,
                        result.get("success", False),
                        tool_duration,
                        arguments=tool_call.arguments,
                    )

                    tool_results.append(result)

                    # Add tool result to conversation for context
                    self.conversation_history.append(
                        Message(
                            role=MessageRole.TOOL,
                            content=f"Tool '{tool_call.name}' result: {result.get('content', '')}",
                        )
                    )

                # If we had tool calls, get a final response from LLM with results
                if tool_results:
                    final_response = await self.llm_service.chat(
                        messages=self.conversation_history
                        + [
                            Message(
                                role=MessageRole.USER,
                                content="Please provide a summary of the results.",
                            )
                        ]
                    )
                    final_content = final_response.content

            # Add assistant response to conversation
            assistant_message = Message(
                role=MessageRole.ASSISTANT, content=final_content
            )
            self.conversation_history.append(assistant_message)

            self.logger.info(
                f"✅ Command processed successfully, response length: {len(final_content)}"
            )
            return final_content

    async def process_command_stream(
        self, user_input: str
    ) -> AsyncGenerator[str, None]:
        """Process a user command and stream response tokens in real-time."""
        with LogPerformance(
            "command_streaming", "jarvis.assistant", command_length=len(user_input)
        ):
            self.logger.info(
                f"💬 Processing strea`ming command: {user_input[:100]}{'...' if len(user_input) > 100 else ''}"
            )

            # Add user message to conversation
            user_message = Message(role=MessageRole.USER, content=user_input)
            self.conversation_history.append(user_message)

            # Get available tools
            tools = await self.mcp_client.list_tools()
            self.logger.debug(f"🔧 Available tools: {[tool['name'] for tool in tools]}")

            # Convert tools to LLM format
            llm_tools = self._convert_tools_for_llm(tools)

            # Check if this might need tool calls (simple heuristic)
            needs_tools = any(
                keyword in user_input.lower()
                for keyword in [
                    "email",
                    "calendar",
                    "schedule",
                    "send",
                    "check",
                    "create",
                    "event",
                    "events",
                    "meeting",
                    "meetings",
                    "next",
                    "upcoming",
                    "today",
                    "tomorrow",
                    "list",
                    "show",
                    "tell",
                    "notification",
                    "reminder",
                    "reminders",
                    "hue",
                    "lights",
                    "light",
                    "color",
                    "brightness",
                    "turn on",
                    "turn off",
                ]
            )

            if llm_tools and needs_tools:
                # Use non-streaming mode when tools are available to allow tool calls
                self.logger.info(
                    f"🛠️  Tools available (needs_tools={needs_tools}), using non-streaming mode to enable tool calling"
                )

                # Get LLM response with potential tool calls
                start_time = datetime.now()
                llm_response = await self.llm_service.chat(
                    messages=self.conversation_history,
                    tools=llm_tools,
                )
                llm_duration = (datetime.now() - start_time).total_seconds()

                self.logger.log_performance(
                    "llm_chat_with_tools",
                    llm_duration,
                    model=self.config.ollama.model,
                    tool_calls=len(llm_response.tool_calls),
                )

                # Execute any tool calls
                if llm_response.tool_calls:
                    self.logger.info(
                        f"🛠️  Executing {len(llm_response.tool_calls)} tool calls"
                    )

                    for tool_call in llm_response.tool_calls:
                        tool_start = datetime.now()
                        result = await self.mcp_client.execute_tool(
                            tool_call.name, tool_call.arguments, tool_call.id
                        )
                        tool_duration = (datetime.now() - tool_start).total_seconds()

                        self.logger.log_tool_execution(
                            tool_call.name,
                            result.get("success", False),
                            tool_duration,
                            arguments=tool_call.arguments,
                        )

                        # Add tool result to conversation for context
                        self.conversation_history.append(
                            Message(
                                role=MessageRole.TOOL,
                                content=f"Tool '{tool_call.name}' result: {result.get('content', '')}",
                            )
                        )

                    # Now stream the final response with tool results
                    summary_message = Message(
                        role=MessageRole.USER,
                        content="Please provide a summary of the results in a natural way.",
                    )

                    full_response = ""
                    async for token in self.llm_service.chat_stream(
                        messages=self.conversation_history + [summary_message]
                    ):
                        full_response += token
                        yield token

                    # Add final response to conversation
                    assistant_message = Message(
                        role=MessageRole.ASSISTANT, content=full_response
                    )
                    self.conversation_history.append(assistant_message)

                else:
                    # No tool calls, just stream the regular response
                    full_response = ""
                    async for token in self.llm_service.chat_stream(
                        messages=self.conversation_history
                    ):
                        full_response += token
                        yield token

                    # Add response to conversation
                    assistant_message = Message(
                        role=MessageRole.ASSISTANT, content=full_response
                    )
                    self.conversation_history.append(assistant_message)

            else:
                # Simple conversation without tools - pure streaming
                self.logger.info("💬 Pure conversation mode, using streaming")

                full_response = ""
                async for token in self.llm_service.chat_stream(
                    messages=self.conversation_history
                ):
                    full_response += token
                    yield token

                # Add response to conversation
                assistant_message = Message(
                    role=MessageRole.ASSISTANT, content=full_response
                )
                self.conversation_history.append(assistant_message)

            self.logger.info(
                f"✅ Streaming command processed successfully, response length: {len(full_response) if 'full_response' in locals() else 'unknown'}"
            )

    async def transcribe_audio(
        self,
        file,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Transcribe audio file using Whisper service."""
        try:
            return await self.whisper_client.transcribe_audio(
                audio_data=await file.read(),
                filename=file.filename or "audio.webm",
                language=language,
                temperature=temperature,
            )
        except Exception as e:
            self.logger.error(f"Audio transcription failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def speak_text(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Convert text to speech using TTS service."""
        try:
            return await self.whisper_client.speak_text(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
            )
        except Exception as e:
            self.logger.error(f"TTS failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def get_services_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        try:
            # Check MCP Orchestrator
            mcp_status = await self.mcp_client.health_check()

            # Check Whisper Service
            whisper_status = await self.whisper_client.health_check()

            # Check LLM Service (basic check)
            llm_status = {"status": "healthy", "model": self.config.ollama.model}

            return {
                "assistant": {"status": "healthy"},
                "mcp_orchestrator": mcp_status,
                "whisper_service": whisper_status,
                "llm_service": llm_status,
            }
        except Exception as e:
            self.logger.error(f"Failed to get services status: {e}", exc_info=True)
            return {
                "assistant": {"status": "error", "error": str(e)},
                "mcp_orchestrator": {"status": "unknown"},
                "whisper_service": {"status": "unknown"},
                "llm_service": {"status": "unknown"},
            }

    def _convert_tools_for_llm(
        self, mcp_tools: List[Dict[str, Any]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Convert MCP tools to LLM function calling format."""
        if not mcp_tools:
            return None

        llm_tools = []
        for tool in mcp_tools:
            llm_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool.get("parameters", {}),
                },
            }
            llm_tools.append(llm_tool)

        return llm_tools

    def clear_conversation(self) -> None:
        """Clear conversation history except system prompt."""
        self.conversation_history = [
            msg for msg in self.conversation_history if msg.role == MessageRole.SYSTEM
        ]

    async def shutdown(self) -> None:
        """Clean shutdown of the assistant."""
        await self.mcp_client.disconnect()
        await self.whisper_client.disconnect()
