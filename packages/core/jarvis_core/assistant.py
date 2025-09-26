"""Main Jarvis assistant orchestrator."""

from datetime import datetime
from typing import List, Optional, AsyncGenerator

from jarvis_shared.config import JarvisConfig
from jarvis_shared.models import Message, MessageRole
from jarvis_shared.logger import get_logger, LogPerformance

from .llm_client import OllamaClient
from .mcp_client import MCPClient


class JarvisAssistant:
    """Main Jarvis assistant that orchestrates LLM and tools."""

    def __init__(self, config: JarvisConfig):
        self.config = config
        self.logger = get_logger("jarvis.assistant")
        self.llm_client = OllamaClient(config.ollama)
        self.mcp_client = MCPClient(config.mcp)
        self.conversation_history: List[Message] = []

        # System prompt for Jarvis
        self.system_prompt = """You are Jarvis, an AI assistant similar to the one from Iron Man. 
You are helpful, intelligent, and can manage emails and calendar events.

You have access to the following tools:
- Gmail: Read emails, send emails
- Google Calendar: List events, create events

Always be very concise and helpful. When using tools, explain what you're doing.
If you need to use multiple tools, do so efficiently."""

    async def initialize(self):
        """Initialize the assistant and connect to services."""
        with LogPerformance("assistant_initialization", "jarvis.assistant"):
            self.logger.info("🚀 Initializing Jarvis Assistant")
            await self.mcp_client.connect()

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

            # Get LLM response
            start_time = datetime.now()
            llm_response = await self.llm_client.chat(
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
                    result = await self.mcp_client.execute_tool(tool_call)
                    tool_duration = (datetime.now() - tool_start).total_seconds()

                    self.logger.log_tool_execution(
                        tool_call.name,
                        result.success,
                        tool_duration,
                        arguments=tool_call.arguments,
                    )

                    tool_results.append(result)

                    # Add tool result to conversation for context
                    self.conversation_history.append(
                        Message(
                            role=MessageRole.TOOL,
                            content=f"Tool '{tool_call.name}' result: {result.content}",
                        )
                    )

                # If we had tool calls, get a final response from LLM with results
                if tool_results:
                    final_response = await self.llm_client.chat(
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
                f"💬 Processing streaming command: {user_input[:100]}{'...' if len(user_input) > 100 else ''}"
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
                ]
            )

            if needs_tools and llm_tools:
                # For tool-requiring requests, use non-streaming first to get tool calls
                self.logger.info(
                    "🛠️  Command may require tools, using non-streaming mode"
                )

                # Get LLM response with potential tool calls
                start_time = datetime.now()
                llm_response = await self.llm_client.chat(
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
                        result = await self.mcp_client.execute_tool(tool_call)
                        tool_duration = (datetime.now() - tool_start).total_seconds()

                        self.logger.log_tool_execution(
                            tool_call.name,
                            result.success,
                            tool_duration,
                            arguments=tool_call.arguments,
                        )

                        # Add tool result to conversation for context
                        self.conversation_history.append(
                            Message(
                                role=MessageRole.TOOL,
                                content=f"Tool '{tool_call.name}' result: {result.content}",
                            )
                        )

                    # Now stream the final response with tool results
                    summary_message = Message(
                        role=MessageRole.USER,
                        content="Please provide a summary of the results in a natural way.",
                    )

                    full_response = ""
                    async for token in self.llm_client.chat_stream(
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
                    async for token in self.llm_client.chat_stream(
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
                async for token in self.llm_client.chat_stream(
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

    def _convert_tools_for_llm(self, mcp_tools: List[dict]) -> Optional[List[dict]]:
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

    def clear_conversation(self):
        """Clear conversation history except system prompt."""
        self.conversation_history = [
            msg for msg in self.conversation_history if msg.role == MessageRole.SYSTEM
        ]

    async def shutdown(self):
        """Clean shutdown of the assistant."""
        await self.mcp_client.disconnect()
