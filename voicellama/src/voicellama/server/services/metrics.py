"""
Prometheus-style Metrics Module

Provides request metrics, latency tracking, and a /metrics endpoint
for monitoring TTS API performance.
"""
import time
import threading
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class HistogramBucket:
    """A histogram bucket for latency tracking."""
    le: float
    count: int = 0


@dataclass
class MetricValue:
    """A metric value with labels."""
    value: float = 0
    labels: Dict[str, str] = field(default_factory=dict)


class Metrics:
    """
    Thread-safe metrics collector with Prometheus-compatible output.

    Tracks:
    - Request counts by endpoint and status
    - Request latency histograms
    - TTS generation metrics (duration, text length)
    - Cache hit/miss rates
    - WebSocket connection counts
    - Error counts by type
    """

    DEFAULT_BUCKETS = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def __init__(self, namespace: str = "voicellama"):
        """Initialize metrics collector."""
        self.namespace = namespace
        self._lock = threading.RLock()

        self._request_count: Dict[str, int] = defaultdict(int)
        self._error_count: Dict[str, int] = defaultdict(int)
        self._tts_generated_count = 0
        self._tts_cached_count = 0
        self._bytes_generated = 0

        self._websocket_connections = 0
        self._models_loaded = 0

        self._request_latency: Dict[str, List[float]] = defaultdict(list)
        self._tts_latency: List[float] = []
        self._tts_text_length: List[int] = []

        self._start_time = time.time()

        self.enabled = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
        self.max_samples = int(os.getenv('METRICS_MAX_SAMPLES', '10000'))

    def inc_request(self, endpoint: str, method: str = "POST", status: int = 200) -> None:
        """Increment request counter."""
        if not self.enabled:
            return
        with self._lock:
            key = f"{method}:{endpoint}:{status}"
            self._request_count[key] += 1

    def inc_error(self, error_type: str) -> None:
        """Increment error counter."""
        if not self.enabled:
            return
        with self._lock:
            self._error_count[error_type] += 1

    def inc_tts_generated(self, cached: bool = False, bytes_size: int = 0) -> None:
        """Increment TTS generation counter."""
        if not self.enabled:
            return
        with self._lock:
            if cached:
                self._tts_cached_count += 1
            else:
                self._tts_generated_count += 1
            self._bytes_generated += bytes_size

    def observe_request_latency(self, endpoint: str, duration_seconds: float) -> None:
        """Record request latency."""
        if not self.enabled:
            return
        with self._lock:
            samples = self._request_latency[endpoint]
            samples.append(duration_seconds)
            if len(samples) > self.max_samples:
                self._request_latency[endpoint] = samples[-self.max_samples:]

    def observe_tts_latency(self, duration_seconds: float, text_length: int) -> None:
        """Record TTS generation latency and text length."""
        if not self.enabled:
            return
        with self._lock:
            self._tts_latency.append(duration_seconds)
            self._tts_text_length.append(text_length)
            if len(self._tts_latency) > self.max_samples:
                self._tts_latency = self._tts_latency[-self.max_samples:]
                self._tts_text_length = self._tts_text_length[-self.max_samples:]

    def set_websocket_connections(self, count: int) -> None:
        """Set current WebSocket connection count."""
        if not self.enabled:
            return
        with self._lock:
            self._websocket_connections = count

    def set_models_loaded(self, count: int) -> None:
        """Set number of loaded models."""
        if not self.enabled:
            return
        with self._lock:
            self._models_loaded = count

    def _calculate_histogram(self, samples: List[float], buckets: List[float] = None) -> Dict[str, float]:
        """Calculate histogram buckets from samples."""
        if not samples:
            return {}

        buckets = buckets or self.DEFAULT_BUCKETS
        result = {}

        for bucket in buckets:
            count = sum(1 for s in samples if s <= bucket)
            result[f"le_{bucket}"] = count

        result["le_+Inf"] = len(samples)
        result["sum"] = sum(samples)
        result["count"] = len(samples)

        return result

    def _calculate_percentiles(self, samples: List[float]) -> Dict[str, float]:
        """Calculate percentiles from samples."""
        if not samples:
            return {}

        sorted_samples = sorted(samples)
        n = len(sorted_samples)

        def percentile(p: float) -> float:
            idx = int(n * p / 100)
            return sorted_samples[min(idx, n - 1)]

        return {
            "p50": percentile(50),
            "p90": percentile(90),
            "p95": percentile(95),
            "p99": percentile(99),
            "min": sorted_samples[0],
            "max": sorted_samples[-1],
            "avg": sum(sorted_samples) / n
        }

    def get_metrics_dict(self) -> dict:
        """Get all metrics as a dictionary."""
        with self._lock:
            uptime = time.time() - self._start_time

            total_requests = sum(self._request_count.values())
            total_errors = sum(self._error_count.values())

            requests_by_endpoint = defaultdict(int)
            requests_by_status = defaultdict(int)
            for key, count in self._request_count.items():
                parts = key.split(":")
                if len(parts) >= 3:
                    endpoint = parts[1]
                    status = parts[2]
                    requests_by_endpoint[endpoint] += count
                    requests_by_status[status] += count

            tts_latency_stats = self._calculate_percentiles(self._tts_latency)
            text_length_stats = self._calculate_percentiles([float(x) for x in self._tts_text_length])

            return {
                "uptime_seconds": round(uptime, 2),
                "requests": {
                    "total": total_requests,
                    "by_endpoint": dict(requests_by_endpoint),
                    "by_status": dict(requests_by_status)
                },
                "errors": {
                    "total": total_errors,
                    "by_type": dict(self._error_count)
                },
                "tts": {
                    "generated": self._tts_generated_count,
                    "cached": self._tts_cached_count,
                    "cache_hit_rate": round(
                        self._tts_cached_count / (self._tts_generated_count + self._tts_cached_count) * 100, 2
                    ) if (self._tts_generated_count + self._tts_cached_count) > 0 else 0,
                    "bytes_generated": self._bytes_generated,
                    "latency": tts_latency_stats,
                    "text_length": text_length_stats
                },
                "connections": {
                    "websocket": self._websocket_connections
                },
                "models": {
                    "loaded": self._models_loaded
                }
            }

    def get_prometheus_format(self) -> str:
        """Get metrics in Prometheus text format."""
        lines = []
        ns = self.namespace

        with self._lock:
            uptime = time.time() - self._start_time

            lines.append(f"# HELP {ns}_uptime_seconds Time since server start")
            lines.append(f"# TYPE {ns}_uptime_seconds gauge")
            lines.append(f"{ns}_uptime_seconds {uptime:.2f}")

            lines.append(f"# HELP {ns}_requests_total Total number of requests")
            lines.append(f"# TYPE {ns}_requests_total counter")
            for key, count in self._request_count.items():
                parts = key.split(":")
                if len(parts) >= 3:
                    method, endpoint, status = parts[0], parts[1], parts[2]
                    lines.append(f'{ns}_requests_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}')

            lines.append(f"# HELP {ns}_errors_total Total number of errors")
            lines.append(f"# TYPE {ns}_errors_total counter")
            for error_type, count in self._error_count.items():
                lines.append(f'{ns}_errors_total{{type="{error_type}"}} {count}')

            lines.append(f"# HELP {ns}_tts_generated_total Total TTS generations")
            lines.append(f"# TYPE {ns}_tts_generated_total counter")
            lines.append(f"{ns}_tts_generated_total {self._tts_generated_count}")

            lines.append(f"# HELP {ns}_tts_cached_total Total cached TTS responses")
            lines.append(f"# TYPE {ns}_tts_cached_total counter")
            lines.append(f"{ns}_tts_cached_total {self._tts_cached_count}")

            lines.append(f"# HELP {ns}_bytes_generated_total Total bytes of audio generated")
            lines.append(f"# TYPE {ns}_bytes_generated_total counter")
            lines.append(f"{ns}_bytes_generated_total {self._bytes_generated}")

            if self._tts_latency:
                lines.append(f"# HELP {ns}_tts_latency_seconds TTS generation latency")
                lines.append(f"# TYPE {ns}_tts_latency_seconds histogram")
                hist = self._calculate_histogram(self._tts_latency)
                for bucket, count in hist.items():
                    if bucket.startswith("le_"):
                        le = bucket[3:]
                        lines.append(f'{ns}_tts_latency_seconds_bucket{{le="{le}"}} {count}')
                    elif bucket == "sum":
                        lines.append(f"{ns}_tts_latency_seconds_sum {count:.4f}")
                    elif bucket == "count":
                        lines.append(f"{ns}_tts_latency_seconds_count {count}")

            lines.append(f"# HELP {ns}_websocket_connections Current WebSocket connections")
            lines.append(f"# TYPE {ns}_websocket_connections gauge")
            lines.append(f"{ns}_websocket_connections {self._websocket_connections}")

            lines.append(f"# HELP {ns}_models_loaded Number of loaded models")
            lines.append(f"# TYPE {ns}_models_loaded gauge")
            lines.append(f"{ns}_models_loaded {self._models_loaded}")

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._request_count.clear()
            self._error_count.clear()
            self._tts_generated_count = 0
            self._tts_cached_count = 0
            self._bytes_generated = 0
            self._request_latency.clear()
            self._tts_latency.clear()
            self._tts_text_length.clear()
            self._start_time = time.time()


# Global metrics instance
metrics = Metrics(namespace="voicellama")
