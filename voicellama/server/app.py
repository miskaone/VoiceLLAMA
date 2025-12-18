"""FastAPI application factory for VoiceLLAMA."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from voicellama.config import Config
from voicellama.server.routes import tts, settings, health, ui
from voicellama.server.middleware import setup_middleware, configure_logging, get_logger
from voicellama.server.services import metrics


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
        description="Ultra-fast Text-to-Speech API powered by Kokoro-82M"
    )

    # Setup middleware (order matters)
    setup_middleware(app, config)

    # Include routers
    app.include_router(health.router)
    app.include_router(tts.router)
    app.include_router(settings.router)
    app.include_router(ui.router)

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files mounted from {static_dir}")

    @app.on_event("startup")
    async def startup():
        logger.info("VoiceLLAMA server starting up")
        # Pre-load the pipeline if desired
        if os.getenv('PRELOAD_MODEL', 'false').lower() == 'true':
            from voicellama.server.routes.tts import load_pipeline
            load_pipeline()

    @app.on_event("shutdown")
    async def shutdown():
        logger.info("VoiceLLAMA server shutting down")

    return app
