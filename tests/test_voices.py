"""Tests for voice listing endpoint."""

import pytest


def test_list_voices(test_client, valid_voices):
    """Test GET /voices returns available voices."""
    response = test_client.get("/voices")
    assert response.status_code == 200

    data = response.json()
    assert "voices" in data
    assert "default" in data

    for voice in valid_voices:
        assert voice in data["voices"]

    assert data["default"] == "af_heart"
