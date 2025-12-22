"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from voicellama.config import Config
from voicellama.server import create_app


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    config = Config()
    config.server.port = 8333
    config.server.host = "127.0.0.1"
    config.server.log_level = "DEBUG"
    config.tts.cache_enabled = False  # Disable cache for tests
    config.server.rate_limit_requests = 1000  # High limit for tests
    return config


@pytest.fixture
def client(test_config: Config) -> TestClient:
    """Create a test client."""
    app = create_app(test_config)
    return TestClient(app)


@pytest.fixture
def mock_pipeline(monkeypatch):
    """Mock the Kokoro pipeline for testing."""
    class MockPipeline:
        def __call__(self, text: str, voice: str = "af_heart", speed: float = 1.0):
            import numpy as np
            # Generate mock audio (0.1 seconds of silence)
            sample_rate = 24000
            duration = 0.1
            samples = int(sample_rate * duration)
            audio = np.zeros(samples, dtype=np.float32)
            yield (None, None, audio)
    
    mock = MockPipeline()
    monkeypatch.setattr("voicellama.server.routes.tts._pipeline", mock)
    monkeypatch.setattr("voicellama.server.routes.tts.load_pipeline", lambda: mock)
    return mock

