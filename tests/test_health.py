"""Tests for health check endpoints."""

import pytest


def test_health_endpoint(test_client):
    """Test the /health endpoint returns expected structure."""
    response = test_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "cache" in data
    assert "queue" in data
    assert "formats" in data


def test_cache_stats_endpoint(test_client):
    """Test the /cache/stats endpoint."""
    response = test_client.get("/cache/stats")
    assert response.status_code == 200

    data = response.json()
    assert "enabled" in data
    assert "entries" in data
    assert "hits" in data
    assert "misses" in data


def test_queue_stats_endpoint(test_client):
    """Test the /queue/stats endpoint."""
    response = test_client.get("/queue/stats")
    assert response.status_code == 200

    data = response.json()
    assert "enabled" in data
    assert "max_concurrent" in data
    assert "current_queue_length" in data


def test_formats_endpoint(test_client):
    """Test the /formats endpoint."""
    response = test_client.get("/formats")
    assert response.status_code == 200

    data = response.json()
    assert "formats" in data
    assert "wav" in data["formats"]
    assert "ffmpeg_available" in data


def test_metrics_json_endpoint(test_client):
    """Test the /metrics/json endpoint."""
    response = test_client.get("/metrics/json")
    assert response.status_code == 200

    data = response.json()
    assert "uptime_seconds" in data
    assert "requests" in data
    assert "tts" in data


def test_metrics_prometheus_endpoint(test_client):
    """Test the /metrics endpoint returns Prometheus format."""
    response = test_client.get("/metrics")
    assert response.status_code == 200
    assert "voicellama_uptime_seconds" in response.text
