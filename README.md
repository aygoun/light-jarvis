# Jarvis AI Assistant

A modular AI assistant with MCP (Model Context Protocol) integration, supporting Gmail, Google Calendar, and system notifications.

## 🚀 Quick Start

1. **Install dependencies:**

   ```bash
   uv sync
   ```

2. **Set up environment variables:**

   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start the MCP server:**

   ```bash
   uv run python scripts/start_mcp_server.py
   ```

4. **Run Jarvis:**
   ```bash
   uv run python jarvis/cli.py
   ```

## 📋 Environment Variables

Jarvis uses environment variables to configure its behavior. All environment variables are prefixed with `JARVIS_` and use double underscores (`__`) for nested configuration.

### 🔧 General Configuration

| Variable                    | Default | Description                                                    |
| --------------------------- | ------- | -------------------------------------------------------------- |
| `JARVIS_GENERAL__DEBUG`     | `false` | Enable debug mode for verbose output                           |
| `JARVIS_GENERAL__LOG_LEVEL` | `DEBUG` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

### 📝 Logging Configuration

| Variable                       | Default             | Description                                                  |
| ------------------------------ | ------------------- | ------------------------------------------------------------ |
| `JARVIS_LOGGING__LEVEL`        | `INFO`              | Log level for the logging system                             |
| `JARVIS_LOGGING__DIR`          | `./logs`            | Directory for log files (organized by date: `logs/YYYY/MM/`) |
| `JARVIS_LOGGING__CONSOLE`      | `false`             | Enable/disable console output (`true`/`false`)               |
| `JARVIS_LOGGING__FILE`         | `true`              | Enable/disable file logging (`true`/`false`)                 |
| `JARVIS_LOGGING__RICH`         | `true`              | Enable/disable rich formatting in console (`true`/`false`)   |
| `JARVIS_LOGGING__MAX_SIZE`     | `10485760`          | Max log file size in bytes before rotation (10MB)            |
| `JARVIS_LOGGING__BACKUP_COUNT` | `5`                 | Number of backup files to keep                               |
| `JARVIS_LOGGING__DATE_FORMAT`  | `%Y-%m-%d %H:%M:%S` | Date format for log entries                                  |

### 🤖 Ollama Configuration

| Variable                     | Default                  | Description                 |
| ---------------------------- | ------------------------ | --------------------------- |
| `JARVIS_OLLAMA__HOST`        | `http://localhost:11434` | Ollama server URL           |
| `JARVIS_OLLAMA__MODEL`       | `llama3.2:3b`            | Ollama model to use         |
| `JARVIS_OLLAMA__TEMPERATURE` | `0.1`                    | Model temperature (0.0-1.0) |
| `JARVIS_OLLAMA__TIMEOUT`     | `120`                    | Request timeout in seconds  |

### 🔌 MCP Server Configuration

| Variable              | Default     | Description                    |
| --------------------- | ----------- | ------------------------------ |
| `JARVIS_MCP__HOST`    | `localhost` | MCP server host                |
| `JARVIS_MCP__PORT`    | `3000`      | MCP server port                |
| `JARVIS_MCP__TIMEOUT` | `30`        | MCP request timeout in seconds |

### 🔐 Google Services Configuration

| Variable                             | Default                             | Description                            |
| ------------------------------------ | ----------------------------------- | -------------------------------------- |
| `JARVIS_GOOGLE__CREDENTIALS_FILE`    | `~/.jarvis/google_credentials.json` | Path to Google OAuth2 credentials file |
| `JARVIS_GOOGLE__TOKEN_FILE`          | `~/.jarvis/google_token.json`       | Path to Google OAuth2 token file       |
| `JARVIS_GOOGLE__OAUTH_CALLBACK_HOST` | `localhost`                         | OAuth2 callback host                   |
| `JARVIS_GOOGLE__OAUTH_CALLBACK_PORT` | `3000`                              | OAuth2 callback port                   |
| `JARVIS_GOOGLE__OAUTH_CALLBACK_PATH` | `/oauth2/callback`                  | OAuth2 callback path                   |
| `JARVIS_GOOGLE__SCOPES`              | See below                           | Google API scopes (comma-separated)    |

#### Google API Scopes

The default Google API scopes are:

- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/calendar.readonly`
- `https://www.googleapis.com/auth/calendar.events`

To override, set `JARVIS_GOOGLE__SCOPES` as a comma-separated list:

```bash
JARVIS_GOOGLE__SCOPES="https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.send"
```

## 📁 Configuration Files

### TOML Configuration (`config/default.toml`)

Jarvis loads default configuration from `config/default.toml`. Environment variables override TOML values.

### Environment File (`.env`)

Create a `.env` file in the project root to set environment variables:

```bash
# Copy the example file
cp env.example .env

# Edit with your values
nano .env
```

## 🛠️ Tool Configuration

Tools are configured in `config/tools.json` and organized by category:

- **Gmail Tools**: Email reading and sending
- **Calendar Tools**: Event management
- **Notification Tools**: System notifications and reminders

## 🔧 Development

### Project Structure

```
jarvis/
├── packages/
│   ├── core/           # Core assistant logic
│   ├── llm-service/    # LLM integration (Ollama)
│   ├── mcp-server/     # MCP server implementation
│   ├── shared/         # Shared utilities and models
│   └── tools/          # Tool implementations
│       ├── gmail-tool/
│       ├── calendar-tool/
│       └── notification-tool/
├── config/             # Configuration files
├── scripts/            # Utility scripts
└── tests/              # Test suite
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
```

### Logging

Logs are organized by date in the `logs/` directory:

```
logs/
└── 2025/
    └── 09/
        ├── 2025_09_26_jarvis.log
        ├── 2025_09_26_jarvis.assistant.log
        ├── 2025_09_26_jarvis.mcp.server.log
        └── ...
```

## 🔐 Google OAuth2 Setup

1. **Create Google Cloud Project:**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable APIs:**

   - Enable Gmail API
   - Enable Google Calendar API

3. **Create OAuth2 Credentials:**

   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Set application type to "Desktop application"
   - Download the JSON file

4. **Configure Jarvis:**

   ```bash
   # Copy credentials to Jarvis config directory
   cp ~/Downloads/your-credentials.json ~/.jarvis/google_credentials.json

   # Set environment variable (optional)
   export JARVIS_GOOGLE__CREDENTIALS_FILE="~/.jarvis/google_credentials.json"
   ```

5. **First Run:**
   - Start the MCP server
   - Jarvis will open a browser for OAuth2 authentication
   - Grant permissions and complete the flow

## 🚀 Deployment

### Production Environment

For production deployment, consider these environment variables:

```bash
# Production settings
JARVIS_GENERAL__DEBUG=false
JARVIS_GENERAL__LOG_LEVEL=INFO
JARVIS_LOGGING__CONSOLE=false
JARVIS_LOGGING__FILE=true
JARVIS_LOGGING__RICH=false

# Secure paths
JARVIS_GOOGLE__CREDENTIALS_FILE=/etc/jarvis/google_credentials.json
JARVIS_GOOGLE__TOKEN_FILE=/etc/jarvis/google_token.json
JARVIS_LOGGING__DIR=/var/log/jarvis
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project
COPY . /app
WORKDIR /app

# Install dependencies
RUN uv sync --frozen

# Set environment variables
ENV JARVIS_LOGGING__DIR=/app/logs
ENV JARVIS_GOOGLE__CREDENTIALS_FILE=/app/config/google_credentials.json

# Expose port
EXPOSE 3000

# Start MCP server
CMD ["uv", "run", "python", "scripts/start_mcp_server.py"]
```

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'jarvis_gmail'"**

   - Ensure all dependencies are installed: `uv sync`
   - Check that tool packages are in the Python path

2. **OAuth2 callback errors**

   - Verify `JARVIS_GOOGLE__OAUTH_CALLBACK_HOST` and `JARVIS_GOOGLE__OAUTH_CALLBACK_PORT`
   - Ensure the MCP server is running before authentication

3. **Ollama connection errors**

   - Check that Ollama is running: `ollama serve`
   - Verify `JARVIS_OLLAMA__HOST` and `JARVIS_OLLAMA__MODEL`

4. **Permission denied errors**
   - Ensure Jarvis has write access to log and config directories
   - Check file permissions for Google credentials

### Debug Mode

Enable debug mode for detailed logging:

```bash
export JARVIS_GENERAL__DEBUG=true
export JARVIS_GENERAL__LOG_LEVEL=DEBUG
export JARVIS_LOGGING__CONSOLE=true
```

## 📚 API Reference

### MCP Server Endpoints

- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /tools/execute` - Execute a tool
- `GET /auth/status` - Authentication status
- `GET /oauth2/callback` - OAuth2 callback

### Tool Categories

#### Gmail Tools

- `gmail_read_emails` - Read and search emails
- `gmail_send_email` - Send emails

#### Calendar Tools

- `calendar_list_events` - List calendar events
- `calendar_create_event` - Create calendar events

#### Notification Tools

- `send_notification` - Send system notifications
- `schedule_reminder` - Schedule reminders
- `cancel_reminder` - Cancel reminders
- `list_reminders` - List scheduled reminders

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM inference
- [Pydantic](https://pydantic.dev/) for configuration management
- [FastAPI](https://fastapi.tiangolo.com/) for the MCP server
- [Rich](https://rich.readthedocs.io/) for beautiful console output
