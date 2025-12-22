"""Tests for settings endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json


@pytest.fixture
def settings_file(tmp_path):
    """Create a temporary settings file."""
    settings_path = tmp_path / "voicellama_settings.json"
    return settings_path


def test_get_settings(client: TestClient):
    """Test getting current settings."""
    response = client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "engine" in data
    assert "voice" in data
    assert "speed" in data
    assert "enabled" in data


def test_update_settings(client: TestClient):
    """Test updating settings."""
    response = client.post(
        "/settings",
        json={
            "voice": "am_adam",
            "speed": 1.2
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["voice"] == "am_adam"
    assert data["speed"] == 1.2


def test_update_settings_validation_invalid_engine(client: TestClient):
    """Test settings validation with invalid engine."""
    response = client.post(
        "/settings",
        json={
            "engine": "invalid_engine"
        }
    )
    assert response.status_code == 422  # Validation error


def test_update_settings_validation_invalid_chatter_level(client: TestClient):
    """Test settings validation with invalid chatter level."""
    response = client.post(
        "/settings",
        json={
            "chatter_level": "invalid_level"
        }
    )
    assert response.status_code == 422  # Validation error


def test_get_context(client: TestClient):
    """Test getting context window state."""
    response = client.get("/context")
    assert response.status_code == 200
    data = response.json()
    assert "used" in data
    assert "total" in data
    assert "percentage" in data


def test_update_context(client: TestClient):
    """Test updating context window state."""
    response = client.post(
        "/context",
        json={
            "used": 50000,
            "total": 200000
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["used"] == 50000
    assert data["total"] == 200000
    assert data["percentage"] == 25.0

