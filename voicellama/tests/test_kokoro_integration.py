"""Integration tests with real Kokoro pipeline."""

import os
import pytest
from fastapi.testclient import TestClient

# Check if Kokoro is available
try:
    from kokoro import KPipeline
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False

# Allow enabling real tests via environment variable
ENABLE_REAL_TESTS = os.getenv("ENABLE_KOKORO_TESTS", "false").lower() == "true"


@pytest.mark.skipif(not KOKORO_AVAILABLE or not ENABLE_REAL_TESTS, reason="Kokoro not available or tests disabled")
@pytest.mark.integration
@pytest.mark.kokoro
class TestRealKokoroIntegration:
    """Integration tests with real Kokoro pipeline."""

    @pytest.fixture(scope="class")
    def real_pipeline(self):
        """Load real Kokoro pipeline."""
        pipeline = KPipeline(lang_code='a')
        return pipeline

    def test_real_tts_generation(self, client: TestClient):
        """Test real TTS generation with Kokoro."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello, this is a real TTS test.",
                "voice": "af_heart",
                "format": "wav"
            }
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("audio/")
        assert len(response.content) > 0

    @pytest.mark.parametrize("voice", [
        "af_heart", "af_bella", "af_sarah",
        "am_adam", "am_michael",
        "bf_emma", "bf_isabella",
        "bm_george", "bm_lewis"
    ])
    def test_all_voices_real(self, client: TestClient, voice):
        """Test all voices with real Kokoro."""
        response = client.post(
            "/tts/announce",
            json={
                "text": f"Testing voice {voice}",
                "voice": voice,
                "format": "wav"
            }
        )
        assert response.status_code == 200
        assert len(response.content) > 0

    @pytest.mark.parametrize("speed", [0.5, 1.0, 1.5, 2.0, 2.5])
    def test_different_speeds_real(self, client: TestClient, speed):
        """Test different speeds with real Kokoro."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Speed test with real pipeline",
                "voice": "af_heart",
                "speed": speed,
                "format": "wav"
            }
        )
        assert response.status_code == 200
        assert len(response.content) > 0

    def test_batch_real_generation(self, client: TestClient):
        """Test batch TTS with real Kokoro."""
        response = client.post(
            "/tts/batch",
            json={
                "items": [
                    {"text": "First item", "voice": "af_heart"},
                    {"text": "Second item", "voice": "am_adam"},
                    {"text": "Third item", "voice": "bf_emma"}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        for result in data["results"]:
            assert result["error"] is None
            assert result["audio_base64"] is not None

    def test_error_handling_real(self, client: TestClient):
        """Test error handling with real pipeline."""
        # Test with invalid text (empty after validation)
        response = client.post(
            "/tts/announce",
            json={
                "text": "   ",
                "voice": "af_heart"
            }
        )
        assert response.status_code == 422

    def test_performance_real(self, client: TestClient, benchmark):
        """Benchmark real Kokoro performance."""
        def make_request():
            return client.post(
                "/tts/announce",
                json={
                    "text": "Performance benchmark with real Kokoro",
                    "voice": "af_heart",
                    "format": "wav"
                }
            )
        
        result = benchmark(make_request)
        assert result.status_code == 200

