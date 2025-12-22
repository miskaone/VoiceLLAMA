"""FastAPI application factory for VoiceLLAMA."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from voicellama.config import Config
from voicellama.server.routes import tts, settings, health, ui
from voicellama.server.middleware import setup_middleware, configure_logging, get_logger
from voicellama.server.services import metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger = get_logger('voicellama')
    
    # Startup
    logger.info("VoiceLLAMA server starting up")
    if os.getenv('PRELOAD_MODEL', 'false').lower() == 'true':
        from voicellama.server.routes.tts import load_pipeline
        load_pipeline()
    
    yield
    
    # Shutdown
    logger.info("VoiceLLAMA server shutting down")


def create_app(config: Config = None) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        config: Optional configuration. If not provided, loads from defaults.

    Returns:
        Configured FastAPI application
    """
    if config is None:
        config = Config.load()

    # Configure logging
    configure_logging(
        level=config.server.log_level,
        json_format=config.server.log_format == 'json'
    )

    logger = get_logger('voicellama')
    logger.info("Creating VoiceLLAMA application")

    app = FastAPI(
        title="VoiceLLAMA TTS API",
        version="0.1.0",
        description="Ultra-fast Text-to-Speech API powered by Kokoro-82M",
        lifespan=lifespan
    )

    # Setup middleware (order matters)
    setup_middleware(app, config)

    # Include routers
    # Legacy routes (deprecated, use /v1/ instead)
    app.include_router(health.router)
    app.include_router(tts.router)
    app.include_router(settings.router)
    app.include_router(ui.router)
    
    # Versioned API routes
    from voicellama.server.routes.v1 import health as v1_health, tts as v1_tts, settings as v1_settings
    app.include_router(v1_health.router, prefix="/v1", tags=["v1"])
    app.include_router(v1_tts.router, prefix="/v1", tags=["v1"])
    app.include_router(v1_settings.router, prefix="/v1", tags=["v1"])

    # Mount static files
    # Static directory is at project root, not in server/
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files mounted from {static_dir}")

    return app
