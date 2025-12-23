# VoiceLLAMA

Ultra-fast Text-to-Speech API Server powered by Kokoro-82M.

VoiceLLAMA provides a production-ready FastAPI server for converting text to speech using the Kokoro TTS model. It features request queuing, response caching, WebSocket streaming, and a web-based UI.

## Requirements

- Python 3.11 or higher
- Kokoro TTS library
- ffmpeg (optional, for MP3/OGG encoding)

## One-Click Installation

### Windows

```batch
# Double-click install.bat
# Or run in PowerShell:
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

## Docker Installation

### Quick Start

```bash
# Using Docker Compose (recommended)
docker compose up -d

# Or build and run directly
docker build -t voicellama .
docker run -p 8333:8333 voicellama
```

### GPU Support

```bash
docker build --target gpu -t voicellama:gpu .
docker run --gpus all -p 8333:8333 voicellama:gpu
```

### Docker Compose Profiles

| Profile | Command | Description |
|---------|---------|-------------|
| (default) | `docker compose up -d` | CPU-only, production |
| `gpu` | `docker compose --profile gpu up -d` | GPU-enabled |
| `dev` | `docker compose --profile dev up` | Development with hot reload |

## Manual Installation

```bash
# Install with Kokoro
pip install -e ".[kokoro]"

# Or install separately
pip install -e .
pip install kokoro
```

## Quick Start

```bash
# Start server
voicellama serve

# Custom port
voicellama serve --port 9000

# With startup sound
STARTUP_SOUND=true voicellama serve
```

Server runs at `http://localhost:8333`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8333 | Server port |
| `HOST` | 0.0.0.0 | Server host |
| `LOG_LEVEL` | INFO | Logging level |
| `LOG_FORMAT` | dev | Log format (dev/json) |
| `PRELOAD_MODEL` | false | Pre-load model on startup |
| `STARTUP_SOUND` | false | Play sound on startup |
| `API_KEY` | - | API key for authentication |
| `CORS_ORIGINS` | - | Allowed CORS origins |
| `TTS_CACHE_ENABLED` | true | Enable response caching |
| `QUEUE_MAX_CONCURRENT` | 2 | Max concurrent TTS jobs |

### Configuration File

Create `voicellama.toml`:

```toml
[server]
port = 8333
host = "0.0.0.0"
log_level = "INFO"
startup_sound = false

[tts]
default_voice = "af_heart"
default_speed = 1.0
cache_enabled = true

[chatter]
level = "summary"
question = true
summary = true
detail = false
```

## Architecture

```
src/voicellama/
├── __main__.py          # CLI entry point
├── config.py            # Configuration management
├── hooks/               # Claude Code integration hooks
├── media/               # Audio assets
├── server/
│   ├── app.py           # FastAPI application factory
│   ├── middleware/      # Logging, security, rate limiting
│   ├── routes/          # API endpoints (v1/, legacy)
│   └── services/        # Cache, queue, metrics, encoding
└── static/              # Web UI files
```

### Design Principles

- **Routes**: Thin API layer delegating to services
- **Services**: Business logic (cache, queue, metrics)
- **Middleware**: Cross-cutting concerns (logging, security)
- **Configuration**: Priority: CLI args > env vars > config file > defaults

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/tts/announce` | POST | Generate TTS audio |
| `/v1/tts/batch` | POST | Batch TTS generation |
| `/v1/voices` | GET | List available voices |
| `/v1/health` | GET | Health check |
| `/v1/settings` | GET/POST | Manage settings |
| `/metrics` | GET | Prometheus metrics |
| `/ws/tts` | WS | Real-time audio streaming |

## Troubleshooting

### Model Not Loading

- Verify Kokoro is installed: `pip install kokoro`
- Set `PRELOAD_MODEL=true` to see startup errors
- Check logs for error messages

### Audio Encoding Fails

- Install ffmpeg for MP3/OGG support
- WAV format works without ffmpeg

### High Memory Usage

- Reduce `TTS_CACHE_MAX_MEMORY_MB`
- Reduce `QUEUE_MAX_CONCURRENT`

## License

MIT

## Support

For issues and questions, open an issue on the project repository.
