"""FastAPI application factory for VoiceLLAMA."""

import os
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from voicellama.config import Config
from voicellama.server.routes import tts, settings, health, ui
from voicellama.server.middleware import setup_middleware, configure_logging, get_logger
from voicellama.server.services import metrics


def _find_audio_player():
    """Find an available audio player for startup sound."""
    import shutil

    # Try to find players using shutil.which (cross-platform)
    for player in ['ffplay', 'ffplay.exe', 'mpv', 'aplay', 'paplay']:
        found = shutil.which(player)
        if found:
            return found

    # Fallback paths for Windows
    win_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffplay.exe"),
        r"C:\Program Files\ffmpeg\bin\ffplay.exe",
        r"C:\ffmpeg\bin\ffplay.exe",
    ]
    for path in win_paths:
        if Path(path).exists():
            return path

    # Fallback for WSL - check common Windows user paths
    if Path("/mnt/c/Users").exists():
        try:
            for user_dir in Path("/mnt/c/Users").iterdir():
                if user_dir.is_dir() and user_dir.name not in ("Public", "Default", "Default User", "All Users"):
                    wsl_ffplay = user_dir / "AppData/Local/Microsoft/WinGet/Links/ffplay.exe"
                    if wsl_ffplay.exists():
                        return str(wsl_ffplay)
        except (PermissionError, OSError):
            pass

    return None


def _play_startup_sound():
    """Play the startup sound if available."""
    # Look for startup sound in media directory
    media_dir = Path(__file__).parent.parent / "media"
    sound_file = media_dir / "winamp-demo.mp3"

    if not sound_file.exists():
        return False

    player = _find_audio_player()
    if not player:
        return False

    try:
        if 'ffplay.exe' in player:
            # Convert WSL path to Windows path for ffplay.exe
            win_path = str(sound_file).replace('/mnt/c', 'C:').replace('/', '\\')
            subprocess.Popen(
                [player, '-nodisp', '-autoexit', '-loglevel', 'quiet', win_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            subprocess.Popen(
                [player, '-nodisp', '-autoexit', '-loglevel', 'quiet', str(sound_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return True
    except Exception:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger = get_logger('voicellama')

    # Startup
    logger.info("VoiceLLAMA server starting up")
    if os.getenv('PRELOAD_MODEL', 'false').lower() == 'true':
        from voicellama.server.routes.tts import load_pipeline
        load_pipeline()

    # Play startup sound if enabled
    if os.getenv('STARTUP_SOUND', 'false').lower() in ('true', '1', 'yes'):
        if _play_startup_sound():
            logger.info("Startup sound played")
        else:
            logger.warning("Startup sound not available")

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
