"""
TTS Response Caching Module

Provides in-memory caching for TTS responses to avoid regenerating
identical audio for repeated requests.
"""
import hashlib
import time
import os
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional, Tuple
import threading


@dataclass
class CacheEntry:
    """A cached TTS response."""
    audio_data: bytes
    sample_rate: int
    created_at: float
    text_length: int
    generation_time_ms: float


class TTSCache:
    """
    LRU cache for TTS responses with TTL support.

    Features:
    - LRU eviction when max_size is reached
    - TTL-based expiration
    - Thread-safe operations
    - Memory-aware (tracks total bytes cached)
    """

    def __init__(
        self,
        max_size: int = 100,
        max_memory_mb: float = 500,
        ttl_seconds: int = 3600,
        enabled: bool = True
    ):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            ttl_seconds: Time-to-live for entries (default 1 hour)
            enabled: Whether caching is enabled
        """
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._total_bytes = 0

        self.hits = 0
        self.misses = 0

    def _make_key(self, text: str, voice: str, speed: float = 1.0, **kwargs) -> str:
        """Generate a unique cache key from request parameters."""
        key_parts = [
            text,
            voice,
            f"speed:{speed:.2f}",
        ]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}:{v}")

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def get(self, text: str, voice: str, speed: float = 1.0, **kwargs) -> Optional[Tuple[bytes, int]]:
        """
        Get cached audio if available.

        Returns:
            Tuple of (audio_bytes, sample_rate) if found, None otherwise
        """
        if not self.enabled:
            return None

        key = self._make_key(text, voice, speed, **kwargs)

        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            entry = self._cache[key]

            if time.time() - entry.created_at > self.ttl_seconds:
                self._remove_entry(key)
                self.misses += 1
                return None

            self._cache.move_to_end(key)
            self.hits += 1

            return (entry.audio_data, entry.sample_rate)

    def put(
        self,
        text: str,
        voice: str,
        audio_data: bytes,
        sample_rate: int,
        speed: float = 1.0,
        generation_time_ms: float = 0,
        **kwargs
    ) -> None:
        """Store audio in the cache."""
        if not self.enabled:
            return

        key = self._make_key(text, voice, speed, **kwargs)
        entry_size = len(audio_data)

        with self._lock:
            if key in self._cache:
                self._remove_entry(key)

            while (
                (len(self._cache) >= self.max_size) or
                (self._total_bytes + entry_size > self.max_memory_bytes)
            ) and self._cache:
                oldest_key = next(iter(self._cache))
                self._remove_entry(oldest_key)

            if entry_size > self.max_memory_bytes:
                return

            self._cache[key] = CacheEntry(
                audio_data=audio_data,
                sample_rate=sample_rate,
                created_at=time.time(),
                text_length=len(text),
                generation_time_ms=generation_time_ms
            )
            self._total_bytes += entry_size

    def _remove_entry(self, key: str) -> None:
        """Remove an entry from the cache (must hold lock)."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._total_bytes -= len(entry.audio_data)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._total_bytes = 0
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "enabled": self.enabled,
                "entries": len(self._cache),
                "max_entries": self.max_size,
                "memory_mb": round(self._total_bytes / 1024 / 1024, 2),
                "max_memory_mb": round(self.max_memory_bytes / 1024 / 1024, 2),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_percent": round(hit_rate, 1),
                "ttl_seconds": self.ttl_seconds
            }

    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        removed = 0
        current_time = time.time()

        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time - entry.created_at > self.ttl_seconds
            ]

            for key in expired_keys:
                self._remove_entry(key)
                removed += 1

        return removed


# Global cache instance
_cache_enabled = os.getenv('TTS_CACHE_ENABLED', 'true').lower() == 'true'
_cache_max_size = int(os.getenv('TTS_CACHE_MAX_SIZE', '100'))
_cache_max_memory_mb = float(os.getenv('TTS_CACHE_MAX_MEMORY_MB', '500'))
_cache_ttl = int(os.getenv('TTS_CACHE_TTL_SECONDS', '3600'))

tts_cache = TTSCache(
    enabled=_cache_enabled,
    max_size=_cache_max_size,
    max_memory_mb=_cache_max_memory_mb,
    ttl_seconds=_cache_ttl
)
