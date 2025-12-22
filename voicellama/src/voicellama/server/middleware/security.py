"""
Security utilities for VoiceLLAMA API server.
Provides CORS configuration, rate limiting, and API key authentication.
"""
import os
import time
import secrets
from collections import defaultdict
from typing import Optional, List

from fastapi import Request, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def get_cors_origins() -> List[str]:
    """
    Get allowed CORS origins from environment.

    In development (default): Allow localhost on common ports
    In production: Set CORS_ORIGINS env var to specific domains
    """
    env_origins = os.getenv('CORS_ORIGINS', '')

    if env_origins:
        origins = [o.strip() for o in env_origins.split(',') if o.strip()]
        return origins

    return [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://localhost:8111",
        "http://localhost:8333",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8111",
        "http://127.0.0.1:8333",
    ]


def get_cors_config() -> dict:
    """Get CORS middleware configuration."""
    origins = get_cors_origins()

    allow_all = os.getenv('CORS_ALLOW_ALL', 'false').lower() == 'true'

    if allow_all:
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

    return {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
    }


# Rate limiting storage (in-memory, per-process)
_rate_limit_storage: dict = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(
        self,
        app,
        requests_per_window: int = None,
        window_seconds: int = None,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.requests_per_window = requests_per_window or int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
        self.window_seconds = window_seconds or int(os.getenv('RATE_LIMIT_WINDOW', '60'))
        self.exclude_paths = exclude_paths or ['/health', '/docs', '/openapi.json']

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (IP address or forwarded IP)."""
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.client.host if request.client else 'unknown'

    def _clean_old_requests(self, client_id: str, now: float):
        """Remove requests outside the current window."""
        cutoff = now - self.window_seconds
        _rate_limit_storage[client_id] = [
            ts for ts in _rate_limit_storage[client_id] if ts > cutoff
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        client_id = self._get_client_id(request)
        now = time.time()

        self._clean_old_requests(client_id, now)

        request_count = len(_rate_limit_storage[client_id])

        if request_count >= self.requests_per_window:
            oldest_request = min(_rate_limit_storage[client_id])
            retry_after = int(self.window_seconds - (now - oldest_request)) + 1

            return Response(
                content=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_window),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(oldest_request + self.window_seconds))
                }
            )

        _rate_limit_storage[client_id].append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(self.requests_per_window - request_count - 1)
        response.headers["X-RateLimit-Reset"] = str(int(now + self.window_seconds))

        return response


# API Key authentication
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> Optional[str]:
    """Get the configured API key from environment."""
    return os.getenv('API_KEY')


def verify_api_key(api_key: str) -> bool:
    """Verify an API key using constant-time comparison."""
    expected_key = get_api_key()
    if not expected_key:
        return True
    return secrets.compare_digest(api_key or '', expected_key)


async def require_api_key(api_key: Optional[str] = Depends(_api_key_header)) -> str:
    """Dependency that requires a valid API key."""
    expected_key = get_api_key()

    if not expected_key:
        return "no-auth"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return api_key


async def optional_api_key(api_key: Optional[str] = Depends(_api_key_header)) -> Optional[str]:
    """Dependency that optionally validates API key."""
    expected_key = get_api_key()

    if not expected_key:
        return None

    if api_key and not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return api_key


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        host = request.headers.get("host", "")
        if not host.startswith("localhost") and not host.startswith("127.0.0.1"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
