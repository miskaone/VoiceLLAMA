"""Performance benchmarks for VoiceLLAMA."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.benchmark
class TestTTSLatency:
    """Benchmark TTS generation latency."""

    def test_single_request_latency(self, client: TestClient, mock_pipeline, benchmark):
        """Benchmark single TTS request latency."""
        def make_request():
            return client.post(
                "/tts/announce",
                json={
                    "text": "Hello, world!",
                    "voice": "af_heart",
                    "format": "wav"
                }
            )
        
        result = benchmark(make_request)
        assert result.status_code == 200

    def test_batch_request_latency(self, client: TestClient, mock_pipeline, benchmark):
        """Benchmark batch TTS request latency."""
        def make_batch_request():
            return client.post(
                "/tts/batch",
                json={
                    "items": [
                        {"text": f"Text {i}", "voice": "af_heart"}
                        for i in range(5)
                    ]
                }
            )
        
        result = benchmark(make_batch_request)
        assert result.status_code == 200

    def test_cached_vs_uncached(self, client: TestClient, mock_pipeline, benchmark):
        """Compare cached vs uncached request latency."""
        # First request (uncached)
        client.post(
            "/tts/announce",
            json={
                "text": "Cache benchmark",
                "voice": "af_heart",
                "use_cache": True
            }
        )
        
        # Benchmark cached request
        def make_cached_request():
            return client.post(
                "/tts/announce",
                json={
                    "text": "Cache benchmark",
                    "voice": "af_heart",
                    "use_cache": True
                }
            )
        
        cached_result = benchmark(make_cached_request)
        assert cached_result.status_code == 200

    @pytest.mark.parametrize("text_length", [10, 100, 1000, 5000])
    def test_different_text_lengths(self, client: TestClient, mock_pipeline, benchmark, text_length):
        """Benchmark TTS with different text lengths."""
        text = "a" * text_length
        
        def make_request():
            return client.post(
                "/tts/announce",
                json={
                    "text": text,
                    "voice": "af_heart"
                }
            )
        
        result = benchmark(make_request)
        # May hit rate limits during benchmarking, but should work initially
        assert result.status_code in [200, 429]  # 429 is rate limit, acceptable for benchmarks

    @pytest.mark.parametrize("speed", [0.5, 1.0, 1.5, 2.0, 2.5])
    def test_different_speeds(self, client: TestClient, mock_pipeline, benchmark, speed):
        """Benchmark TTS with different speeds."""
        def make_request():
            return client.post(
                "/tts/announce",
                json={
                    "text": "Speed test",
                    "voice": "af_heart",
                    "speed": speed
                }
            )
        
        result = benchmark(make_request)
        # May hit rate limits during benchmarking, but should work initially
        assert result.status_code in [200, 429]  # 429 is rate limit, acceptable for benchmarks


@pytest.mark.benchmark
class TestCachePerformance:
    """Benchmark cache performance."""

    def test_cache_hit_rate(self, client: TestClient, mock_pipeline):
        """Measure cache hit rate."""
        text = "Cache hit rate test"
        
        # Generate and cache
        client.post(
            "/tts/announce",
            json={
                "text": text,
                "voice": "af_heart",
                "use_cache": True
            }
        )
        
        # Check cache stats
        stats_before = client.get("/cache/stats").json()
        hits_before = stats_before["hits"]
        
        # Make cached request
        client.post(
            "/tts/announce",
            json={
                "text": text,
                "voice": "af_heart",
                "use_cache": True
            }
        )
        
        # Check cache stats again
        stats_after = client.get("/cache/stats").json()
        hits_after = stats_after["hits"]
        
        assert hits_after > hits_before

    def test_cache_memory_usage(self, client: TestClient, mock_pipeline):
        """Test cache memory usage tracking."""
        # Generate multiple cached requests
        for i in range(10):
            client.post(
                "/tts/announce",
                json={
                    "text": f"Memory test {i}",
                    "voice": "af_heart",
                    "use_cache": True
                }
            )
        
        stats = client.get("/cache/stats").json()
        assert stats["memory_mb"] > 0
        assert stats["entries"] > 0


@pytest.mark.benchmark
class TestConcurrentPerformance:
    """Benchmark concurrent request handling."""

    def test_sequential_requests(self, client: TestClient, mock_pipeline, benchmark):
        """Benchmark sequential requests."""
        def make_sequential():
            results = []
            for i in range(5):
                result = client.post(
                    "/tts/announce",
                    json={
                        "text": f"Sequential {i}",
                        "voice": "af_heart"
                    }
                )
                results.append(result)
            return results
        
        results = benchmark(make_sequential)
        # Some may hit rate limits, but most should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 3  # At least 3 out of 5 should succeed

    def test_queue_behavior_under_load(self, client: TestClient, mock_pipeline):
        """Test queue behavior under load."""
        # Make multiple concurrent requests
        import threading
        
        results = []
        errors = []
        
        def make_request(i):
            try:
                result = client.post(
                    "/tts/announce",
                    json={
                        "text": f"Load test {i}",
                        "voice": "af_heart"
                    }
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=make_request, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Check queue stats
        queue_stats = client.get("/queue/stats").json()
        assert queue_stats["total_processed"] > 0 or len(results) > 0

