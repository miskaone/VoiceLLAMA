"""
Request Queue Module

Provides request queuing and concurrency limiting for TTS generation
to prevent server overload.
"""
import asyncio
import time
import os
from dataclasses import dataclass
from typing import Optional, Callable, Any
from enum import Enum


class QueueStatus(str, Enum):
    """Status of a queued request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class QueuedRequest:
    """A request in the queue."""
    id: str
    created_at: float
    status: QueueStatus = QueueStatus.PENDING
    position: int = 0
    result: Optional[Any] = None
    error: Optional[str] = None


class RequestQueue:
    """
    Async request queue with concurrency limiting.

    Features:
    - Configurable max concurrent requests
    - Queue size limits
    - Request timeout
    - Position tracking for waiting clients
    - Graceful degradation under load
    """

    def __init__(
        self,
        max_concurrent: int = None,
        max_queue_size: int = None,
        request_timeout: float = None,
        enabled: bool = None
    ):
        """
        Initialize the request queue.

        Args:
            max_concurrent: Max simultaneous TTS generations
            max_queue_size: Max pending requests in queue
            request_timeout: Timeout for queued requests (seconds)
            enabled: Whether queuing is enabled
        """
        self.max_concurrent = max_concurrent or int(os.getenv('QUEUE_MAX_CONCURRENT', '2'))
        self.max_queue_size = max_queue_size or int(os.getenv('QUEUE_MAX_SIZE', '50'))
        self.request_timeout = request_timeout or float(os.getenv('QUEUE_TIMEOUT', '60'))
        self.enabled = enabled if enabled is not None else os.getenv('QUEUE_ENABLED', 'true').lower() == 'true'

        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        self._active_count = 0
        self._total_processed = 0
        self._total_rejected = 0
        self._total_timeouts = 0

    @property
    def queue_length(self) -> int:
        """Current number of requests in queue."""
        return self._queue.qsize()

    @property
    def active_count(self) -> int:
        """Current number of active requests."""
        return self._active_count

    @property
    def is_full(self) -> bool:
        """Check if queue is at capacity."""
        return self._queue.full()

    def get_stats(self) -> dict:
        """Get queue statistics."""
        return {
            "enabled": self.enabled,
            "max_concurrent": self.max_concurrent,
            "max_queue_size": self.max_queue_size,
            "request_timeout": self.request_timeout,
            "current_queue_length": self.queue_length,
            "active_requests": self._active_count,
            "total_processed": self._total_processed,
            "total_rejected": self._total_rejected,
            "total_timeouts": self._total_timeouts,
            "available_slots": self.max_concurrent - self._active_count
        }

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with queue management.

        If queuing is disabled, executes immediately.
        If queue is full, raises an exception.
        """
        if not self.enabled:
            return await func(*args, **kwargs)

        if self.is_full:
            self._total_rejected += 1
            from fastapi import HTTPException
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Server busy",
                    "message": "Request queue is full. Please try again later.",
                    "queue_length": self.queue_length,
                    "retry_after": 5
                }
            )

        start_time = time.time()

        try:
            acquired = await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.request_timeout
            )

            if not acquired:
                self._total_timeouts += 1
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=504,
                    detail="Request timed out waiting in queue"
                )

            self._active_count += 1

            try:
                result = await func(*args, **kwargs)
                self._total_processed += 1
                return result
            finally:
                self._active_count -= 1
                self._semaphore.release()

        except asyncio.TimeoutError:
            self._total_timeouts += 1
            from fastapi import HTTPException
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "Request timeout",
                    "message": f"Request timed out after {self.request_timeout}s",
                    "waited_seconds": round(time.time() - start_time, 2)
                }
            )

    def get_position(self) -> int:
        """Get estimated queue position for a new request."""
        return self.queue_length + self._active_count + 1

    def get_estimated_wait(self, avg_request_time: float = 1.0) -> float:
        """Estimate wait time for a new request."""
        position = self.get_position()
        batches = (position - 1) // self.max_concurrent
        return batches * avg_request_time


# Global queue instance
request_queue = RequestQueue()
