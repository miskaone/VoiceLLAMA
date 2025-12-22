"""Health check and metrics endpoints."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from voicellama.server.services import tts_cache, request_queue, metrics, audio_encoder

router = APIRouter(tags=["health"])


def get_model_status() -> dict:
    """Check if the TTS model is loaded and ready."""
    try:
        from voicellama.server.routes.tts import _pipeline
        return {
            "loaded": _pipeline is not None,
            "ready": _pipeline is not None,
            "model": "Kokoro-82M"
        }
    except Exception:
        return {
            "loaded": False,
            "ready": False,
            "model": "Kokoro-82M",
            "error": "Unable to check model status"
        }


@router.get("/health")
async def health():
    """Server health check."""
    model_status = get_model_status()
    
    # Determine overall health status
    overall_status = "ok" if model_status.get("ready", False) else "degraded"
    
    return {
        "status": overall_status,
        "version": "0.1.0",
        "model": model_status,
        "cache": tts_cache.get_stats(),
        "queue": request_queue.get_stats(),
        "formats": audio_encoder.get_supported_formats()
    }


@router.get("/metrics", response_class=PlainTextResponse)
async def get_metrics_prometheus():
    """Get metrics in Prometheus format."""
    return metrics.get_prometheus_format()


@router.get("/metrics/json")
async def get_metrics_json():
    """Get metrics as JSON."""
    return metrics.get_metrics_dict()


@router.get("/queue/stats")
async def get_queue_stats():
    """Get request queue statistics."""
    return request_queue.get_stats()


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    return tts_cache.get_stats()


@router.post("/cache/clear")
async def clear_cache():
    """Clear the TTS cache."""
    tts_cache.clear()
    return {"status": "ok", "message": "Cache cleared"}


@router.get("/formats")
async def get_supported_formats():
    """Get supported audio output formats."""
    return {
        "formats": audio_encoder.get_supported_formats(),
        "ffmpeg_available": audio_encoder.ffmpeg_available,
        "details": {
            fmt: audio_encoder.get_format_info(fmt)
            for fmt in audio_encoder.FORMATS
        }
    }
