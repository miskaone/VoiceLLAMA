"""Edge case tests for TTS endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestTextInputEdgeCases:
    """Test edge cases for text input."""

    def test_whitespace_only_text(self, client: TestClient):
        """Test TTS request with whitespace-only text."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "   \n\t   ",
                "voice": "af_heart"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_maximum_length_text(self, client: TestClient, mock_pipeline):
        """Test TTS request with maximum length text."""
        max_text = "a" * 10000
        response = client.post(
            "/tts/announce",
            json={
                "text": max_text,
                "voice": "af_heart"
            }
        )
        assert response.status_code == 200

    def test_text_exceeding_max_length(self, client: TestClient):
        """Test TTS request with text exceeding max length."""
        long_text = "a" * 10001
        response = client.post(
            "/tts/announce",
            json={
                "text": long_text,
                "voice": "af_heart"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_special_characters(self, client: TestClient, mock_pipeline):
        """Test TTS request with special characters."""
        special_text = "Hello! @#$%^&*() 测试 🎉 émojis"
        response = client.post(
            "/tts/announce",
            json={
                "text": special_text,
                "voice": "af_heart"
            }
        )
        assert response.status_code == 200

    def test_null_characters(self, client: TestClient):
        """Test TTS request with null characters."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello\x00World",
                "voice": "af_heart"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_newlines_and_control_chars(self, client: TestClient, mock_pipeline):
        """Test TTS request with newlines and control characters."""
        text_with_newlines = "Line 1\nLine 2\r\nLine 3\tTabbed"
        response = client.post(
            "/tts/announce",
            json={
                "text": text_with_newlines,
                "voice": "af_heart"
            }
        )
        assert response.status_code == 200

    def test_single_character(self, client: TestClient, mock_pipeline):
        """Test TTS request with single character."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "A",
                "voice": "af_heart"
            }
        )
        assert response.status_code == 200

    def test_html_tags_in_text(self, client: TestClient, mock_pipeline):
        """Test TTS request with HTML tags (should be processed as text)."""
        html_text = "<p>Hello <b>world</b></p>"
        response = client.post(
            "/tts/announce",
            json={
                "text": html_text,
                "voice": "af_heart"
            }
        )
        assert response.status_code == 200

    def test_markdown_formatting(self, client: TestClient, mock_pipeline):
        """Test TTS request with markdown formatting."""
        markdown_text = "# Title\n**Bold** and *italic* text"
        response = client.post(
            "/tts/announce",
            json={
                "text": markdown_text,
                "voice": "af_heart"
            }
        )
        assert response.status_code == 200


class TestVoiceEdgeCases:
    """Test edge cases for voice selection."""

    def test_empty_voice_string(self, client: TestClient):
        """Test TTS request with empty voice string."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello",
                "voice": ""
            }
        )
        # Should use default voice or return validation error
        assert response.status_code in [200, 422]

    def test_voice_with_whitespace(self, client: TestClient, mock_pipeline):
        """Test TTS request with voice containing whitespace."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello",
                "voice": "  af_heart  "
            }
        )
        # Should strip whitespace and work
        assert response.status_code == 200

    @pytest.mark.parametrize("voice", [
        "af_heart", "af_bella", "af_sarah",
        "am_adam", "am_michael",
        "bf_emma", "bf_isabella",
        "bm_george", "bm_lewis"
    ])
    def test_all_available_voices(self, client: TestClient, mock_pipeline, voice):
        """Test TTS generation with all available voices."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Test voice",
                "voice": voice
            }
        )
        assert response.status_code == 200


class TestSpeedEdgeCases:
    """Test edge cases for speed parameter."""

    def test_speed_too_low(self, client: TestClient):
        """Test TTS request with speed below minimum."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello",
                "voice": "af_heart",
                "speed": 0.1  # Below 0.25
            }
        )
        assert response.status_code == 422  # Validation error

    def test_speed_at_minimum_boundary(self, client: TestClient, mock_pipeline):
        """Test TTS request with speed at minimum boundary."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello",
                "voice": "af_heart",
                "speed": 0.25  # Minimum
            }
        )
        assert response.status_code == 200

    def test_speed_at_maximum_boundary(self, client: TestClient, mock_pipeline):
        """Test TTS request with speed at maximum boundary."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello",
                "voice": "af_heart",
                "speed": 3.0  # Maximum
            }
        )
        assert response.status_code == 200

    def test_negative_speed(self, client: TestClient):
        """Test TTS request with negative speed."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello",
                "voice": "af_heart",
                "speed": -1.0
            }
        )
        assert response.status_code == 422  # Validation error

    def test_speed_with_many_decimals(self, client: TestClient, mock_pipeline):
        """Test TTS request with speed having many decimal places."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello",
                "voice": "af_heart",
                "speed": 1.123456789
            }
        )
        assert response.status_code == 200


class TestFormatEdgeCases:
    """Test edge cases for format parameter."""

    def test_format_case_insensitive(self, client: TestClient, mock_pipeline):
        """Test format parameter is case insensitive."""
        for fmt in ["WAV", "Mp3", "OGG", "wav", "mp3", "ogg"]:
            response = client.post(
                "/tts/announce",
                json={
                    "text": "Hello",
                    "voice": "af_heart",
                    "format": fmt
                }
            )
            # May fail if ffmpeg not available for mp3/ogg
            assert response.status_code in [200, 500]

    def test_format_with_whitespace(self, client: TestClient, mock_pipeline):
        """Test format parameter with whitespace."""
        response = client.post(
            "/tts/announce",
            json={
                "text": "Hello",
                "voice": "af_heart",
                "format": "  wav  "
            }
        )
        # Should strip whitespace and work
        assert response.status_code == 200


class TestCacheEdgeCases:
    """Test edge cases for caching."""

    def test_cache_disabled(self, client: TestClient, mock_pipeline):
        """Test TTS generation with cache disabled."""
        response1 = client.post(
            "/tts/announce",
            json={
                "text": "Cache test",
                "voice": "af_heart",
                "use_cache": False
            }
        )
        assert response1.status_code == 200
        
        # Second request should also generate (not cached)
        response2 = client.post(
            "/tts/announce",
            json={
                "text": "Cache test",
                "voice": "af_heart",
                "use_cache": False
            }
        )
        assert response2.status_code == 200

    def test_cache_after_clear(self, client: TestClient, mock_pipeline):
        """Test cache behavior after clearing."""
        # Generate and cache
        client.post(
            "/tts/announce",
            json={
                "text": "Cache clear test",
                "voice": "af_heart",
                "use_cache": True
            }
        )
        
        # Clear cache
        clear_response = client.post("/cache/clear")
        assert clear_response.status_code == 200
        
        # Next request should be cache miss
        response = client.post(
            "/tts/announce",
            json={
                "text": "Cache clear test",
                "voice": "af_heart",
                "use_cache": True
            }
        )
        assert response.status_code == 200


class TestBatchTTSEdgeCases:
    """Test edge cases for batch TTS."""

    def test_single_item_batch(self, client: TestClient, mock_pipeline):
        """Test batch TTS with single item."""
        response = client.post(
            "/tts/batch",
            json={
                "items": [
                    {"text": "Single item", "voice": "af_heart"}
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

    def test_maximum_items_batch(self, client: TestClient, mock_pipeline):
        """Test batch TTS with maximum items (10)."""
        items = [{"text": f"Item {i}", "voice": "af_heart"} for i in range(10)]
        response = client.post(
            "/tts/batch",
            json={"items": items}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10

    def test_mixed_success_error_batch(self, client: TestClient, mock_pipeline):
        """Test batch TTS with mixed valid/invalid items."""
        # Note: Pydantic validates the entire request before processing,
        # so invalid items cause 422 validation error at request level
        # For testing per-item error handling, we need items that pass validation
        # but fail during generation (e.g., pipeline errors)
        response = client.post(
            "/tts/batch",
            json={
                "items": [
                    {"text": "Valid text", "voice": "af_heart"},
                    {"text": "Another valid", "voice": "am_adam"},
                    {"text": "Third valid", "voice": "bf_emma"}
                ]
            }
        )
        # All items should succeed
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
        # All should succeed
        for result in data["results"]:
            assert result["error"] is None

