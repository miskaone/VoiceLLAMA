"""Edge case tests for settings endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_speed_boundary_minimum(client: TestClient):
    """Test settings update with minimum speed boundary."""
    response = client.post(
        "/settings",
        json={"speed": 0.25}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["speed"] == 0.25


def test_speed_boundary_maximum(client: TestClient):
    """Test settings update with maximum speed boundary."""
    response = client.post(
        "/settings",
        json={"speed": 3.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["speed"] == 3.0


def test_speed_below_minimum(client: TestClient):
    """Test settings update with speed below minimum."""
    response = client.post(
        "/settings",
        json={"speed": 0.1}
    )
    assert response.status_code == 422  # Validation error


def test_speed_above_maximum(client: TestClient):
    """Test settings update with speed above maximum."""
    response = client.post(
        "/settings",
        json={"speed": 5.0}
    )
    assert response.status_code == 422  # Validation error


def test_invalid_chatter_level(client: TestClient):
    """Test settings update with invalid chatter level."""
    response = client.post(
        "/settings",
        json={"chatter_level": "invalid"}
    )
    assert response.status_code == 422  # Validation error


def test_custom_states_validation(client: TestClient):
    """Test custom states validation."""
    response = client.post(
        "/settings",
        json={
            "chatter_level": "custom",
            "custom_states": {
                "question": True,
                "summary": False,
                "detail": True
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["chatter_level"] == "custom"
    assert data["custom_states"]["question"] is True
    assert data["custom_states"]["summary"] is False
    assert data["custom_states"]["detail"] is True

