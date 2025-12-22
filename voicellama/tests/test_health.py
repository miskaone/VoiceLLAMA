"""Tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test the health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "model" in data
    assert "cache" in data
    assert "queue" in data
    assert "formats" in data


def test_health_model_status(client: TestClient):
    """Test that health endpoint includes model status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    model_info = data["model"]
    assert "loaded" in model_info
    assert "ready" in model_info
    assert "model" in model_info


def test_metrics_endpoint(client: TestClient):
    """Test the Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    content = response.text
    assert "voicellama" in content


def test_metrics_json_endpoint(client: TestClient):
    """Test the JSON metrics endpoint."""
    response = client.get("/metrics/json")
    assert response.status_code == 200
    data = response.json()
    assert "uptime_seconds" in data
    assert "requests" in data
    assert "tts" in data


def test_queue_stats_endpoint(client: TestClient):
    """Test the queue stats endpoint."""
    response = client.get("/queue/stats")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "max_concurrent" in data
    assert "current_queue_length" in data


def test_cache_stats_endpoint(client: TestClient):
    """Test the cache stats endpoint."""
    response = client.get("/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "entries" in data
    assert "hits" in data
    assert "misses" in data


def test_clear_cache_endpoint(client: TestClient):
    """Test the cache clear endpoint."""
    response = client.post("/cache/clear")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_formats_endpoint(client: TestClient):
    """Test the formats endpoint."""
    response = client.get("/formats")
    assert response.status_code == 200
    data = response.json()
    assert "formats" in data
    assert "ffmpeg_available" in data
    assert isinstance(data["formats"], list)
    assert "wav" in data["formats"]

