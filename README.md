# Jarvis - AI Assistant with Clean Architecture

A modern AI assistant built with a clean, service-oriented architecture. Jarvis provides speech-to-text, text-to-speech, and intelligent tool integration capabilities.

## 🏗️ Architecture

The project is organized into three main services:

### 1. MCP Orchestrator (`packages/mcp-orchestrator/`)

- **Port**: 3000
- **Purpose**: Consolidates all MCP tools (Gmail, Calendar, Notifications)
- **Features**:
  - Unified MCP interface
  - Google authentication management
  - Tool execution coordination

### 2. Whisper Service (`packages/whisper-service/`)

- **Port**: 3001
- **Purpose**: Dedicated STT/TTS functionality
- **Features**:
  - Speech-to-Text using Whisper.cpp
  - Text-to-Speech using Edge-TTS
  - Audio processing and conversion

### 3. Main Orchestrator (`packages/main-orchestrator/`)

- **Port**: 3002
- **Purpose**: Coordinates all services
- **Features**:
  - LLM integration (Ollama)
  - Service coordination
  - Chat interface
  - Streaming responses

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Ollama running locally
- FFmpeg installed (for audio processing)
- Whisper.cpp compiled and available

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd light-jarvis
   ```

2. **Install dependencies**:

   ```bash
   uv sync
   ```

3. **Set up Whisper.cpp**:

   ```bash
   # Follow the whisper.cpp setup instructions
   # Ensure the model is available at models/ggml-base.en.bin
   ```

4. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

### Running the Services

#### Option 1: Start All Services (Recommended)

```bash
python scripts/start_all_services.py
```

#### Option 2: Start Services Individually

1. **Start MCP Orchestrator**:

   ```bash
   python scripts/start_mcp_orchestrator.py
   ```

2. **Start Whisper Service**:

   ```bash
   python scripts/start_whisper_service.py
   ```

3. **Start Main Orchestrator**:
   ```bash
   python scripts/start_main_orchestrator.py
   ```

#### Option 3: Use the CLI

```bash
# Chat with Jarvis
jarvis chat "Hello, what can you help me with?"

# Start the server
jarvis server

# Stream responses
jarvis chat "Check my emails" --stream
```

## 🔧 Configuration

Configuration is managed through `config/default.toml` and environment variables:

```toml
[ollama]
host = "http://localhost:11434"
model = "llama3.2:3b"
temperature = 0.1

[mcp]
host = "localhost"
port = 3000

[whisper]
model_path = "models/ggml-base.en.bin"
whisper_cpp_path = "whisper.cpp/main"
language = "en"

[tts]
engine = "edge"
voice = "en-US-AriaNeural"
rate = 200
volume = 0.8

[google]
credentials_file = "~/.jarvis/google_credentials.json"
scopes = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events"
]
```

## 📡 API Endpoints

### Main Orchestrator (Port 3002)

- `POST /chat` - Send a chat message
- `POST /chat/stream` - Stream chat responses
- `POST /stt/transcribe` - Transcribe audio
- `POST /tts/speak` - Convert text to speech
- `GET /services/status` - Check all services status

### MCP Orchestrator (Port 3000)

- `GET /tools` - List available tools
- `POST /tools/execute` - Execute a tool
- `POST /auth/google` - Authenticate with Google
- `GET /auth/status` - Check authentication status

### Whisper Service (Port 3001)

- `POST /stt/transcribe` - Transcribe audio file
- `POST /stt/transcribe-raw` - Transcribe raw audio data
- `POST /tts/speak` - Convert text to speech
- `POST /tts/save` - Save speech to file
- `GET /tts/voices` - List available voices

## 🛠️ Available Tools

Jarvis has access to the following tools:

### Gmail Tools

- `gmail_read_emails` - Read and search emails
- `gmail_send_email` - Send emails

### Calendar Tools

- `calendar_list_events` - List calendar events
- `calendar_create_event` - Create new events

### Notification Tools

- `send_notification` - Send system notifications
- `schedule_reminder` - Schedule reminder notifications
- `cancel_reminder` - Cancel scheduled reminders
- `list_reminders` - List all scheduled reminders

## 🔍 Development

### Project Structure

```
packages/
├── shared/                 # Shared utilities and models
├── llm-service/           # LLM integration (Ollama)
├── mcp-orchestrator/      # MCP tools consolidation
├── whisper-service/       # STT/TTS functionality
├── main-orchestrator/     # Main coordination service
└── tools/                 # Individual tool implementations
    ├── gmail-tool/
    ├── calendar-tool/
    └── notification-tool/
```

### Adding New Tools

1. Create a new tool package in `packages/tools/`
2. Implement the tool interface
3. Register the tool in the MCP Orchestrator
4. Update the system prompt in the Main Orchestrator

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
```

## 🐛 Troubleshooting

### Common Issues

1. **Whisper.cpp not found**:

   - Ensure whisper.cpp is compiled and in your PATH
   - Check the `whisper_cpp_path` configuration

2. **Model not found**:

   - Download the Whisper model to `models/ggml-base.en.bin`
   - Verify the `model_path` configuration

3. **FFmpeg not found**:

   - Install FFmpeg: `brew install ffmpeg` (macOS)
   - Ensure it's in your PATH

4. **Google authentication fails**:
   - Check your Google credentials file
   - Verify OAuth callback URL configuration

### Logs

Logs are stored in `logs/` directory with daily rotation. Check the latest log files for detailed error information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) for speech-to-text
- [Edge-TTS](https://github.com/rany2/edge-tts) for text-to-speech
- [Ollama](https://ollama.ai/) for local LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
