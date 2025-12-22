"""Error scenario tests."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_pipeline_loading_failure(client: TestClient):
    """Test behavior when pipeline fails to load."""
    with patch("voicellama.server.routes.tts.load_pipeline") as mock_load:
        mock_load.side_effect = ImportError("Kokoro not available")
        
        response = client.post(
            "/tts/announce",
            json={
                "text": "Test",
                "voice": "af_heart"
            }
        )
        # Should return 500 error
        assert response.status_code == 500


def test_pipeline_generation_failure(client: TestClient):
    """Test behavior when pipeline generation fails."""
    class FailingPipeline:
        def __call__(self, text: str, voice: str = "af_heart", speed: float = 1.0):
            raise RuntimeError("Generation failed")
    
    with patch("voicellama.server.routes.tts._pipeline", FailingPipeline()):
        response = client.post(
            "/tts/announce",
            json={
                "text": "Test",
                "voice": "af_heart"
            }
        )
        # Should return 500 error
        assert response.status_code == 500


def test_queue_full_scenario(client: TestClient, mock_pipeline):
    """Test behavior when request queue is full."""
    # This would require mocking the queue to be full
    # For now, we test the queue stats endpoint
    response = client.get("/queue/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "max_queue_size" in stats
    assert "current_queue_length" in stats


def test_batch_with_pipeline_failure(client: TestClient):
    """Test batch TTS when pipeline fails for some items."""
    class PartiallyFailingPipeline:
        call_count = 0
        
        def __call__(self, text: str, voice: str = "af_heart", speed: float = 1.0):
            import numpy as np
            self.call_count += 1
            if self.call_count == 2:  # Fail on second call
                raise RuntimeError("Generation failed")
            # Return mock audio
            audio = np.zeros(2400, dtype=np.float32)
            yield (None, None, audio)
    
    with patch("voicellama.server.routes.tts.load_pipeline", return_value=PartiallyFailingPipeline()):
        response = client.post(
            "/tts/batch",
            json={
                "items": [
                    {"text": "First", "voice": "af_heart"},
                    {"text": "Second", "voice": "af_heart"},
                    {"text": "Third", "voice": "af_heart"}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        # First and third should succeed, second should have error
        assert data["results"][0]["error"] is None
        assert data["results"][1]["error"] is not None
        assert data["results"][2]["error"] is None

