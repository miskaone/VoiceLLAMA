"""Tests for settings endpoints."""

import pytest


def test_get_settings(test_client, sample_settings):
    """Test GET /settings returns default settings."""
    response = test_client.get("/settings")
    assert response.status_code == 200

    data = response.json()
    assert data["engine"] == sample_settings["engine"]
    assert data["voice"] == sample_settings["voice"]
    assert data["speed"] == sample_settings["speed"]


def test_update_voice_setting(test_client):
    """Test updating voice setting."""
    response = test_client.post(
        "/settings",
        json={"voice": "am_adam"}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["voice"] == "am_adam"


def test_update_speed_setting(test_client):
    """Test updating speed setting."""
    response = test_client.post(
        "/settings",
        json={"speed": 1.5}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["speed"] == 1.5


def test_update_chatter_level(test_client, valid_chatter_levels):
    """Test updating chatter level setting."""
    for level in valid_chatter_levels:
        response = test_client.post(
            "/settings",
            json={"chatter_level": level}
        )
        assert response.status_code == 200
        assert response.json()["chatter_level"] == level


def test_invalid_speed_too_low(test_client):
    """Test that speed below minimum is rejected."""
    response = test_client.post(
        "/settings",
        json={"speed": 0.1}
    )
    assert response.status_code == 422


def test_invalid_speed_too_high(test_client):
    """Test that speed above maximum is rejected."""
    response = test_client.post(
        "/settings",
        json={"speed": 5.0}
    )
    assert response.status_code == 422


def test_invalid_chatter_level(test_client):
    """Test that invalid chatter level is rejected."""
    response = test_client.post(
        "/settings",
        json={"chatter_level": "invalid"}
    )
    assert response.status_code == 422


def test_context_endpoint(test_client):
    """Test GET /context returns context state."""
    response = test_client.get("/context")
    assert response.status_code == 200

    data = response.json()
    assert "used" in data
    assert "total" in data
    assert "percentage" in data


def test_update_context(test_client):
    """Test POST /context updates context state."""
    response = test_client.post(
        "/context",
        json={"used": 50000, "total": 200000}
    )
    assert response.status_code == 200

    data = response.json()
    assert data["used"] == 50000
    assert data["total"] == 200000
    assert data["percentage"] == 25.0
