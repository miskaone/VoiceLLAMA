"""
Standardized logging configuration for VoiceLLAMA.
Supports both development (human-readable) and production (JSON) formats.
"""
import logging
import sys
import uuid
import json
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for request correlation
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_request_id() -> str:
    """Get current request ID or generate a new one."""
    rid = request_id_var.get()
    if rid is None:
        rid = str(uuid.uuid4())[:8]
        request_id_var.set(rid)
    return rid


def set_request_id(rid: str) -> None:
    """Set request ID for current context."""
    request_id_var.set(rid)


class CorrelationFilter(logging.Filter):
    """Add correlation ID to all log records."""

    def filter(self, record):
        record.request_id = request_id_var.get() or '-'
        return True


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments."""

    def format(self, record):
        log_obj = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', '-'),
        }

        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)

        extra_fields = [
            'duration_ms', 'text_length', 'text_preview', 'model_type',
            'device', 'ws_clients', 'voice', 'speed', 'method', 'path',
            'status_code', 'error', 'cached', 'format', 'size_kb'
        ]
        for key in extra_fields:
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)

        return json.dumps(log_obj)


class DevFormatter(logging.Formatter):
    """Human-readable formatter for development."""

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)8s] [%(request_id)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )


def configure_logging(
    level: str = 'INFO',
    json_format: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format (for production)
        log_file: Optional file path for logging
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    root_logger.handlers.clear()

    formatter = JSONFormatter() if json_format else DevFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationFilter())
    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(JSONFormatter())
        file_handler.addFilter(CorrelationFilter())
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.error').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that adds request ID and logs request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())[:8]
        set_request_id(request_id)

        logger = get_logger('voicellama.api')

        start_time = time.time()
        logger.info(
            f"{request.method} {request.url.path}",
            extra={'method': request.method, 'path': str(request.url.path)}
        )

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Completed {response.status_code} in {duration_ms:.1f}ms",
            extra={'status_code': response.status_code, 'duration_ms': round(duration_ms, 1)}
        )

        response.headers['X-Request-ID'] = request_id
        return response
