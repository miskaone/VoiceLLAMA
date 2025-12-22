"""Server middleware package."""

from .logging import (
    configure_logging,
    get_logger,
    RequestLoggingMiddleware,
    get_request_id,
    set_request_id,
)
from .security import (
    get_cors_config,
    get_cors_origins,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    require_api_key,
    optional_api_key,
)

__all__ = [
    'configure_logging',
    'get_logger',
    'RequestLoggingMiddleware',
    'get_request_id',
    'set_request_id',
    'get_cors_config',
    'get_cors_origins',
    'RateLimitMiddleware',
    'SecurityHeadersMiddleware',
    'require_api_key',
    'optional_api_key',
]


def setup_middleware(app, config):
    """Setup all middleware for the FastAPI app."""
    from fastapi.middleware.cors import CORSMiddleware

    # Order matters - first added = last executed

    # 1. Request logging (outermost - logs all requests)
    app.add_middleware(RequestLoggingMiddleware)

    # 2. Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=config.server.rate_limit_requests,
        window_seconds=config.server.rate_limit_window,
        exclude_paths=['/health', '/docs', '/openapi.json', '/favicon.ico']
    )

    # 4. CORS
    cors_config = get_cors_config()
    if config.server.cors_allow_all:
        cors_config = {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
    elif config.server.cors_origins:
        cors_config["allow_origins"] = config.server.cors_origins

    app.add_middleware(CORSMiddleware, **cors_config)
