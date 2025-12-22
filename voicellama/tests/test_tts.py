"""Tests for TTS endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_list_voices(client: TestClient):
    """Test listing available voices."""
    response = client.get("/voices")
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert "default" in data
    assert isinstance(data["voices"], dict)
    assert len(data["voices"]) > 0


def test_announce_text_success(client: TestClient, mock_pipeline):
    """Test successful TTS generation."""
    response = client.post(
        "/tts/announce",
        json={
            "text": "Hello, world!",
            "voice": "af_heart",
            "speed": 1.0,
            "format": "wav"
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert len(response.content) > 0


def test_announce_text_validation_empty(client: TestClient):
    """Test TTS request validation with empty text."""
    response = client.post(
        "/tts/announce",
        json={
            "text": "",
            "voice": "af_heart"
        }
    )
    assert response.status_code == 422  # Validation error


def test_announce_text_validation_invalid_voice(client: TestClient):
    """Test TTS request validation with invalid voice."""
    response = client.post(
        "/tts/announce",
        json={
            "text": "Hello",
            "voice": "invalid_voice"
        }
    )
    assert response.status_code == 422  # Validation error


def test_announce_text_validation_speed_range(client: TestClient):
    """Test TTS request validation with invalid speed."""
    response = client.post(
        "/tts/announce",
        json={
            "text": "Hello",
            "voice": "af_heart",
            "speed": 5.0  # Too high
        }
    )
    assert response.status_code == 422  # Validation error


def test_batch_tts_success(client: TestClient, mock_pipeline):
    """Test successful batch TTS generation."""
    response = client.post(
        "/tts/batch",
        json={
            "items": [
                {
                    "text": "First text",
                    "voice": "af_heart"
                },
                {
                    "text": "Second text",
                    "voice": "am_adam"
                }
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_duration_ms" in data
    assert "cached_count" in data
    assert len(data["results"]) == 2
    
    # Check result structure
    for result in data["results"]:
        assert "text" in result
        assert "format" in result
        assert "cached" in result
        assert "size_bytes" in result
        assert "error" in result


def test_batch_tts_empty_list(client: TestClient):
    """Test batch TTS with empty items list."""
    response = client.post(
        "/tts/batch",
        json={
            "items": []
        }
    )
    assert response.status_code == 422  # Validation error


def test_batch_tts_too_many_items(client: TestClient):
    """Test batch TTS with too many items."""
    items = [{"text": f"Text {i}"} for i in range(11)]
    response = client.post(
        "/tts/batch",
        json={"items": items}
    )
    assert response.status_code == 422  # Validation error

