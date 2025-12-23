# VoiceLLAMA

Ultra-fast Text-to-Speech API Server powered by Kokoro-82M.

VoiceLLAMA provides a production-ready FastAPI server for converting text to speech using the Kokoro TTS model. It features request queuing, response caching, WebSocket streaming, comprehensive metrics, and a web-based UI.

## Features

- 🚀 **High Performance**: Optimized for low-latency TTS generation
- 💾 **Smart Caching**: LRU cache with TTL to avoid regenerating identical audio
- 📊 **Metrics & Monitoring**: Prometheus-compatible metrics endpoint
- 🔄 **Request Queuing**: Configurable concurrency limits and queue management
- 🌐 **WebSocket Support**: Real-time audio streaming to connected clients
- 🎨 **Web UI**: Built-in settings and avatar pages
- 🔒 **Security**: Rate limiting, CORS, API key authentication, security headers
- 📝 **Structured Logging**: JSON logging for production, human-readable for development

## Requirements

- Python 3.11 or higher
- Kokoro TTS library (install separately)
- ffmpeg (optional, for MP3/OGG encoding)

## One-Click Installation

The fastest way to get started is using the one-click installer:

### Windows

```batch
# Option 1: Double-click
install.bat

# Option 2: PowerShell
.\install.ps1
```

### Linux / macOS / WSL

```bash
chmod +x install.sh
./install.sh
```

### Installer Options

| Option | Description |
|--------|-------------|
| `--no-hooks` | Skip Claude Code hooks configuration |
| `--no-venv` | Install globally (not recommended) |
| `--dev` | Install development dependencies |
| `--start` | Start server after installation |

Example:
```bash
./install.sh --dev --start
```

The installer will:
1. Check for Python 3.11+
2. Create a virtual environment
3. Install VoiceLLAMA and Kokoro
4. Configure Claude Code hooks (optional)
5. Create start scripts

## Docker Installation

Run VoiceLLAMA in a container with all dependencies included:

### Quick Start (CPU)

```bash
# Using Docker Compose (recommended)
docker compose up -d

# Or build and run directly
docker build -t voicellama .
docker run -p 8333:8333 voicellama
```

### GPU Support

```bash
# Build GPU image
docker build --target gpu -t voicellama:gpu .

# Run with GPU
docker run --gpus all -p 8333:8333 voicellama:gpu

# Or using Docker Compose
docker compose --profile gpu up -d
```

### Docker Compose Profiles

| Profile | Command | Description |
|---------|---------|-------------|
| (default) | `docker compose up -d` | CPU-only, production |
| `gpu` | `docker compose --profile gpu up -d` | GPU-enabled |
| `dev` | `docker compose --profile dev up` | Development with hot reload |

### Persistent Model Cache

The Kokoro model (~200MB) is cached in a Docker volume. To persist across container rebuilds:

```bash
# Model cache is automatically persisted in 'voicellama-cache' volume
docker compose up -d

# View volume
docker volume ls | grep voicellama
```

### Environment Variables

Configure via `docker-compose.yml` or pass directly:

```bash
docker run -p 8333:8333 \
  -e LOG_LEVEL=DEBUG \
  -e PRELOAD_MODEL=true \
  -e API_KEY=your-secret-key \
  voicellama
```

## Manual Installation

### Using pip

```bash
pip install -e .
```

### Using uv (recommended)

```bash
uv pip install -e .
```

### Install Kokoro (REQUIRED)

**Kokoro is REQUIRED for VoiceLLAMA to function.** The Kokoro TTS library must be installed separately. 

**Option 1: Install with optional dependencies**
```bash
pip install -e ".[kokoro]"
```

**Option 2: Install Kokoro separately**
```bash
pip install kokoro
```

Please refer to the [Kokoro documentation](https://github.com/kokoro-ai/kokoro) for detailed installation instructions.

**Note:** Without Kokoro installed, TTS requests will fail with a clear error message.

## Quick Start

### Basic Usage

Start the server with default settings:

```bash
voicellama serve
```

The server will start on `http://0.0.0.0:8333` by default.

### Custom Configuration

```bash
# Custom port
voicellama serve --port 9000

# Localhost only
voicellama serve --host 127.0.0.1

# Custom config file
voicellama serve --config /path/to/voicellama.toml

# Custom log level
voicellama serve --log-level DEBUG
```

### Environment Variables

- `PORT`: Server port (default: 8333)
- `HOST`: Server host (default: 0.0.0.0)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Log format - "dev" or "json" (default: dev)
- `PRELOAD_MODEL`: Pre-load model on startup (default: false)
- `API_KEY`: Optional API key for authentication
- `CORS_ALLOW_ALL`: Allow all CORS origins (default: false)
- `CORS_ORIGINS`: Comma-separated list of allowed origins
- `RATE_LIMIT_REQUESTS`: Requests per window (default: 100)
- `RATE_LIMIT_WINDOW`: Rate limit window in seconds (default: 60)
- `TTS_CACHE_ENABLED`: Enable response caching (default: true)
- `TTS_CACHE_MAX_SIZE`: Max cache entries (default: 100)
- `TTS_CACHE_MAX_MEMORY_MB`: Max cache memory in MB (default: 500)
- `TTS_CACHE_TTL_SECONDS`: Cache TTL in seconds (default: 3600)
- `QUEUE_ENABLED`: Enable request queuing (default: true)
- `QUEUE_MAX_CONCURRENT`: Max concurrent TTS generations (default: 2)
- `QUEUE_MAX_SIZE`: Max queue size (default: 50)
- `QUEUE_TIMEOUT`: Request timeout in seconds (default: 60)

## Configuration File

Create a `voicellama.toml` file in the project root:

```toml
[server]
port = 8333
host = "0.0.0.0"
log_level = "INFO"
log_format = "dev"
rate_limit_requests = 100
rate_limit_window = 60
cors_allow_all = false
cors_origins = ["http://localhost:3000"]

[tts]
default_voice = "af_heart"
default_speed = 1.0
enabled = true
cache_enabled = true
cache_ttl = 3600

[avatar]
enabled = false

[chatter]
level = "sparse"
question = true
summary = false
detail = false
```

## API Documentation

### API Versioning

VoiceLLAMA supports API versioning. The current version is **v1**.

- **Versioned endpoints**: `/v1/tts/announce`, `/v1/health`, etc.
- **Legacy endpoints**: `/tts/announce`, `/health`, etc. (deprecated, use `/v1/` prefix)
- **Version header**: `Accept: application/vnd.voicellama.v1+json` (optional)

All new integrations should use the `/v1/` prefix. Legacy endpoints will be maintained for backward compatibility but may be removed in future versions.

### Endpoints

#### Generate TTS

**Versioned endpoint (recommended):**
```http
POST /v1/tts/announce
```

**Legacy endpoint (deprecated):**
```http
POST /tts/announce
Content-Type: application/json

{
  "text": "Hello, world!",
  "voice": "af_heart",
  "speed": 1.0,
  "format": "wav",
  "use_cache": true
}
```

**Response**: Audio file (WAV, MP3, or OGG)

#### Batch TTS

**Versioned endpoint (recommended):**
```http
POST /v1/tts/batch
```

**Legacy endpoint (deprecated):**
```http
POST /tts/batch
Content-Type: application/json

{
  "items": [
    {
      "text": "First text",
      "voice": "af_heart",
      "speed": 1.0
    },
    {
      "text": "Second text",
      "voice": "am_adam",
      "speed": 1.2
    }
  ]
}
```

**Response**:
```json
{
  "results": [
    {
      "text": "First text",
      "audio_base64": "...",
      "format": "wav",
      "cached": false,
      "size_bytes": 12345,
      "generation_ms": 234.5,
      "error": null
    }
  ],
  "total_duration_ms": 500.0,
  "cached_count": 0
}
```

#### List Available Voices

**Versioned endpoint (recommended):**
```http
GET /v1/voices
```

**Legacy endpoint (deprecated):**
```http
GET /voices
```

**Response**:
```json
{
  "voices": {
    "af_heart": "American Female (Heart) - Warm, expressive",
    "af_bella": "American Female (Bella)",
    ...
  },
  "default": "af_heart"
}
```

#### Health Check

**Versioned endpoint (recommended):**
```http
GET /v1/health
```

**Legacy endpoint (deprecated):**
```http
GET /health
```

**Response**:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "model": "Kokoro-82M",
  "cache": {...},
  "queue": {...},
  "formats": ["wav", "mp3", "ogg"]
}
```

#### Metrics (Prometheus)

```http
GET /metrics
```

Returns metrics in Prometheus text format. (No versioning - internal endpoint)

#### Metrics (JSON)

```http
GET /metrics/json
```

Returns metrics as JSON. (No versioning - internal endpoint)

#### Settings

**Versioned endpoints (recommended):**
```http
GET /v1/settings
POST /v1/settings
```

**Legacy endpoints (deprecated):**
```http
GET /settings
POST /settings
```

Manage TTS settings (voice, speed, chatter level, etc.).

### WebSocket

Connect to `/ws/tts` for real-time audio streaming:

```javascript
const ws = new WebSocket('ws://localhost:8333/ws/tts');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'audio') {
    // Handle audio data
    const audio = new Audio('data:audio/wav;base64,' + data.audio);
    audio.play();
  }
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

## Available Voices

- `af_heart`: American Female (Heart) - Warm, expressive
- `af_bella`: American Female (Bella)
- `af_sarah`: American Female (Sarah)
- `am_adam`: American Male (Adam)
- `am_michael`: American Male (Michael)
- `bf_emma`: British Female (Emma)
- `bf_isabella`: British Female (Isabella)
- `bm_george`: British Male (George)
- `bm_lewis`: British Male (Lewis)

## Web UI

Access the web interface at:

- Settings: `http://localhost:8333/`
- Avatar: `http://localhost:8333/avatar`

## Hooks

VoiceLLAMA includes command-line hooks for integration with other tools:

### Announce Hook

```bash
python -m voicellama.hooks.announce "Your text here" [question|summary|detail]
```

Respects chatter level settings from the API.

## Development

### Project Structure

```
voicellama/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point
├── config.py            # Configuration management
├── hooks/               # Command-line hooks
│   ├── announce.py
│   └── ...
├── server/              # FastAPI application
│   ├── app.py           # Application factory
│   ├── middleware/     # Middleware (logging, security)
│   ├── routes/          # API routes
│   └── services/        # Business logic (cache, queue, metrics)
├── static/              # Web UI files
└── tests/               # Test suite
    ├── conftest.py      # Pytest fixtures
    ├── test_health.py   # Health endpoint tests
    ├── test_tts.py      # TTS endpoint tests
    ├── test_settings.py  # Settings endpoint tests
    ├── test_tts_edge_cases.py  # Edge case tests
    ├── test_settings_edge_cases.py  # Settings edge cases
    ├── test_error_scenarios.py  # Error handling tests
    ├── test_performance.py  # Performance benchmarks
    ├── test_integration.py  # Integration tests
    └── test_kokoro_integration.py  # Real Kokoro tests
```

### Running Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run only unit tests
pytest -m "not integration"

# Run only integration tests
pytest -m integration

# Run performance benchmarks
pytest --benchmark-only

# Run tests with real Kokoro (if available)
ENABLE_KOKORO_TESTS=true pytest -m kokoro

# Run with coverage
pytest --cov=voicellama --cov-report=html

# Run edge case tests
pytest tests/test_tts_edge_cases.py tests/test_settings_edge_cases.py

# Run error scenario tests
pytest tests/test_error_scenarios.py
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking (optional)
mypy voicellama/ --ignore-missing-imports
```

### CI/CD

The project includes GitHub Actions workflows for:
- Linting and format checking
- Running tests on Python 3.11 and 3.12
- Type checking (optional)

See `.github/workflows/ci.yml` for details.

## Architecture

- **Routes**: Thin API layer that delegates to services
- **Services**: Business logic (cache, queue, metrics, audio encoding)
- **Middleware**: Cross-cutting concerns (logging, security, rate limiting)
- **Configuration**: Environment variables, config file, CLI args (priority order)

## Performance Considerations

- **Caching**: Enable caching for repeated requests to reduce generation time
- **Queue**: Adjust `QUEUE_MAX_CONCURRENT` based on your hardware
- **Preloading**: Set `PRELOAD_MODEL=true` to load model on startup
- **Format**: Use MP3 or OGG for smaller file sizes (requires ffmpeg)

## Security

- Rate limiting is enabled by default (100 requests/minute)
- API key authentication is optional (set `API_KEY` env var)
- CORS is configured for development (localhost) by default
- Security headers are added to all responses
- Path traversal protection for static file serving

## Troubleshooting

### Model Not Loading

- Ensure Kokoro is installed: `pip install kokoro`
- Check logs for error messages
- Try setting `PRELOAD_MODEL=true` to see startup errors

### Audio Encoding Fails

- Ensure ffmpeg is installed for MP3/OGG support
- Check `ffmpeg -version` in terminal
- WAV format works without ffmpeg

### High Memory Usage

- Reduce `TTS_CACHE_MAX_MEMORY_MB`
- Reduce `TTS_CACHE_MAX_SIZE`
- Reduce `QUEUE_MAX_CONCURRENT`

### WebSocket Disconnections

- Check network stability
- Implement reconnection logic in client
- Monitor `/metrics/json` for connection counts

## License

MIT

## Contributing

Contributions are welcome! Please ensure:

- Code follows existing style (120 char line length, double quotes)
- Type hints are included
- Docstrings follow Google style
- Tests are added for new features

## Support

For issues and questions, please open an issue on the project repository.

