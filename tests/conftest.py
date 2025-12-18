"""
Pytest configuration and fixtures for VoiceLLAMA tests.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Mock environment variables before importing the app
os.environ.setdefault('LOG_LEVEL', 'WARNING')
os.environ.setdefault('LOG_FORMAT', 'dev')
os.environ.setdefault('CORS_ALLOW_ALL', 'true')


@pytest.fixture(scope="session")
def mock_pipeline():
    """Mock the Kokoro pipeline to avoid loading the actual model."""
    mock = MagicMock()

    def mock_generate(text, voice, speed):
        import numpy as np
        duration = max(1, len(text) // 10)
        sample_rate = 24000
        audio = np.zeros(sample_rate * duration, dtype=np.float32)
        yield ("grapheme", "phoneme", audio)

    mock.return_value = mock_generate
    mock.__call__ = mock_generate
    return mock


@pytest.fixture(scope="function")
def temp_settings_file():
    """Create a temporary settings file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        default_settings = {
            "engine": "kokoro",
            "voice": "af_heart",
            "speed": 1.0,
            "enabled": True,
            "avatar_enabled": False,
            "chatter_level": "sparse",
            "custom_states": {
                "question": True,
                "summary": False,
                "detail": False
            }
        }
        json.dump(default_settings, f)
        temp_path = f.name

    yield temp_path

    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture(scope="function")
def test_client(mock_pipeline, temp_settings_file):
    """Create a test client with mocked dependencies."""
    from fastapi.testclient import TestClient

    with patch('voicellama.server.routes.tts.load_pipeline', return_value=mock_pipeline):
        with patch('voicellama.server.routes.settings.SETTINGS_FILE', Path(temp_settings_file)):
            from voicellama.server import create_app
            from voicellama.config import Config

            config = Config()
            app = create_app(config)

            client = TestClient(app)
            yield client


@pytest.fixture
def sample_settings():
    """Sample settings for testing."""
    return {
        "engine": "kokoro",
        "voice": "af_heart",
        "speed": 1.0,
        "enabled": True,
        "avatar_enabled": False,
        "chatter_level": "sparse",
        "custom_states": {
            "question": True,
            "summary": False,
            "detail": False
        }
    }


@pytest.fixture
def valid_voices():
    """List of valid voice names."""
    return [
        "af_heart", "af_bella", "af_sarah",
        "am_adam", "am_michael",
        "bf_emma", "bf_isabella",
        "bm_george", "bm_lewis"
    ]


@pytest.fixture
def valid_engines():
    """List of valid engine names."""
    return ["kokoro"]


@pytest.fixture
def valid_chatter_levels():
    """List of valid chatter level values."""
    return ["sparse", "summary", "verbose", "custom"]
