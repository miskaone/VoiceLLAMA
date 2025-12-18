# VoiceLLAMA

Ultra-fast TTS API Server powered by [Kokoro-82M](https://github.com/hexgrad/kokoro).

## Quick Start

```bash
# Install
pip install voicellama

# Start server
voicellama serve

# Open http://localhost:8333 for web UI
# API docs at http://localhost:8333/docs
```

## Installation

### From PyPI (recommended)
```bash
pip install voicellama
```

### From source
```bash
git clone https://github.com/miskaone/VoiceLLAMA.git
cd VoiceLLAMA
pip install -e .
```

### Prerequisites
- Python 3.10+
- [espeak-ng](https://github.com/espeak-ng/espeak-ng) (for phoneme conversion)

**Windows:**
```bash
# Download and install from:
# https://github.com/espeak-ng/espeak-ng/releases
```

**Linux:**
```bash
apt-get install espeak-ng
```

**macOS:**
```bash
brew install espeak-ng
```

## Usage

### Start the Server

```bash
# Default (port 8333)
voicellama serve

# Custom port
voicellama serve --port 9000

# With config file
voicellama serve --config voicellama.toml

# Debug logging
voicellama serve --log-level DEBUG
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server health check |
| `/voices` | GET | List available voices |
| `/tts/announce` | POST | Generate TTS audio |
| `/tts/batch` | POST | Batch TTS generation |
| `/settings` | GET/POST | View/update settings |
| `/metrics` | GET | Prometheus metrics |
| `/docs` | GET | OpenAPI documentation |

### Generate Speech

```bash
curl -X POST http://localhost:8333/tts/announce \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "voice": "af_heart"}' \
  --output speech.wav
```

### Python Client

```python
import requests

response = requests.post(
    "http://localhost:8333/tts/announce",
    json={
        "text": "Hello from VoiceLLAMA!",
        "voice": "af_heart",
        "speed": 1.0,
        "format": "wav"
    }
)

with open("speech.wav", "wb") as f:
    f.write(response.content)
```

## Available Voices

| Voice ID | Description |
|----------|-------------|
| `af_heart` | American Female (Heart) - Warm, expressive (default) |
| `af_bella` | American Female (Bella) |
| `af_sarah` | American Female (Sarah) |
| `am_adam` | American Male (Adam) |
| `am_michael` | American Male (Michael) |
| `bf_emma` | British Female (Emma) |
| `bf_isabella` | British Female (Isabella) |
| `bm_george` | British Male (George) |
| `bm_lewis` | British Male (Lewis) |

## Configuration

Create a `voicellama.toml` file:

```toml
[server]
port = 8333
host = "0.0.0.0"
log_level = "INFO"
log_format = "dev"  # or "json" for production

[server.rate_limit]
requests = 100
window = 60

[tts]
default_voice = "af_heart"
default_speed = 1.0
cache_enabled = true
cache_ttl = 3600
```

Or use environment variables:
```bash
export PORT=8333
export LOG_LEVEL=DEBUG
export CORS_ALLOW_ALL=true
voicellama serve
```

## Features

- **Ultra-fast TTS** - Powered by Kokoro-82M (82 million parameters)
- **Multiple voices** - 9 high-quality voices (American/British, Male/Female)
- **Multiple formats** - WAV, MP3, OGG output (MP3/OGG require ffmpeg)
- **Response caching** - LRU cache with TTL for repeated requests
- **Rate limiting** - Configurable per-IP rate limits
- **WebSocket support** - Real-time TTS streaming
- **Prometheus metrics** - Built-in monitoring
- **Web UI** - Settings and avatar pages included

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with auto-reload
uvicorn voicellama.server:create_app --factory --reload --port 8333
```

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Acknowledgements

- [Kokoro](https://github.com/hexgrad/kokoro) - The underlying TTS model
- [hexgrad](https://huggingface.co/hexgrad) - Kokoro model creator
