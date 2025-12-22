"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_full_tts_workflow(client: TestClient, mock_pipeline):
    """Test a complete TTS workflow."""
    # 1. Check health
    health_response = client.get("/health")
    assert health_response.status_code == 200
    
    # 2. List voices
    voices_response = client.get("/voices")
    assert voices_response.status_code == 200
    voices_data = voices_response.json()
    assert len(voices_data["voices"]) > 0
    
    # 3. Generate TTS
    tts_response = client.post(
        "/tts/announce",
        json={
            "text": "Integration test",
            "voice": list(voices_data["voices"].keys())[0],
            "format": "wav"
        }
    )
    assert tts_response.status_code == 200
    assert len(tts_response.content) > 0
    
    # 4. Check metrics
    metrics_response = client.get("/metrics/json")
    assert metrics_response.status_code == 200
    metrics_data = metrics_response.json()
    assert metrics_data["tts"]["generated"] > 0 or metrics_data["tts"]["cached"] > 0


@pytest.mark.integration
def test_batch_tts_workflow(client: TestClient, mock_pipeline):
    """Test batch TTS workflow."""
    # Generate batch TTS
    batch_response = client.post(
        "/tts/batch",
        json={
            "items": [
                {"text": "First", "voice": "af_heart"},
                {"text": "Second", "voice": "am_adam"},
                {"text": "Third", "voice": "bf_emma"}
            ]
        }
    )
    assert batch_response.status_code == 200
    batch_data = batch_response.json()
    assert len(batch_data["results"]) == 3
    
    # Verify all results have required fields
    for result in batch_data["results"]:
        assert "text" in result
        assert "audio_base64" in result
        assert "format" in result
        assert "error" in result
        # Should succeed with mock pipeline
        assert result["error"] is None or result["audio_base64"] is not None


@pytest.mark.integration
def test_settings_workflow(client: TestClient):
    """Test settings management workflow."""
    # Get initial settings
    get_response = client.get("/settings")
    assert get_response.status_code == 200
    initial_settings = get_response.json()
    
    # Update settings
    update_response = client.post(
        "/settings",
        json={
            "voice": "am_adam",
            "speed": 1.1
        }
    )
    assert update_response.status_code == 200
    updated_settings = update_response.json()
    assert updated_settings["voice"] == "am_adam"
    assert updated_settings["speed"] == 1.1
    
    # Verify settings persisted
    get_response2 = client.get("/settings")
    assert get_response2.status_code == 200
    final_settings = get_response2.json()
    assert final_settings["voice"] == "am_adam"
    assert final_settings["speed"] == 1.1


@pytest.mark.integration
def test_cache_workflow(client: TestClient, mock_pipeline):
    """Test cache workflow."""
    # Clear cache
    clear_response = client.post("/cache/clear")
    assert clear_response.status_code == 200
    
    # Check cache stats
    stats_response = client.get("/cache/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["entries"] == 0
    
    # Generate TTS (should populate cache)
    tts_response = client.post(
        "/tts/announce",
        json={
            "text": "Cache test",
            "voice": "af_heart",
            "use_cache": True
        }
    )
    assert tts_response.status_code == 200
    
    # Check cache stats again
    stats_response2 = client.get("/cache/stats")
    assert stats_response2.status_code == 200

