"""TTS generation endpoints."""

import asyncio
import base64
import time
from typing import Optional, List, Set

import numpy as np
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from voicellama.server.services import tts_cache, request_queue, metrics, audio_encoder
from voicellama.server.middleware import get_logger

router = APIRouter(tags=["tts"])
logger = get_logger('voicellama.tts')

# Global pipeline and websocket clients
_pipeline = None
websocket_clients: Set[WebSocket] = set()
_websocket_lock = asyncio.Lock()  # Lock for thread-safe WebSocket client management

# Available voices
AVAILABLE_VOICES = {
    "af_heart": "American Female (Heart) - Warm, expressive",
    "af_bella": "American Female (Bella)",
    "af_sarah": "American Female (Sarah)",
    "am_adam": "American Male (Adam)",
    "am_michael": "American Male (Michael)",
    "bf_emma": "British Female (Emma)",
    "bf_isabella": "British Female (Isabella)",
    "bm_george": "British Male (George)",
    "bm_lewis": "British Male (Lewis)",
}
DEFAULT_VOICE = "af_heart"


def load_pipeline():
    """Load and return the Kokoro pipeline."""
    global _pipeline
    if _pipeline is None:
        from kokoro import KPipeline
        logger.info("Loading Kokoro pipeline")
        _pipeline = KPipeline(lang_code='a')
        logger.info("Pipeline loaded successfully")
        metrics.set_models_loaded(1)
    return _pipeline


class TTSRequest(BaseModel):
    """TTS request with input validation."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text to convert to speech (1-10000 characters)"
    )
    voice: Optional[str] = Field(
        default=DEFAULT_VOICE,
        description="Voice to use for synthesis"
    )
    speed: Optional[float] = Field(
        default=1.0,
        ge=0.25,
        le=3.0,
        description="Speech speed multiplier (0.25-3.0)"
    )
    format: Optional[str] = Field(
        default="wav",
        description="Output format: wav, mp3, ogg"
    )
    use_cache: Optional[bool] = Field(
        default=True,
        description="Use response cache for repeated requests"
    )

    @field_validator('text')
    @classmethod
    def validate_text_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Text cannot be empty or whitespace only")
        if '\x00' in v:
            raise ValueError("Text contains invalid null characters")
        return v

    @field_validator('voice')
    @classmethod
    def validate_voice_name(cls, v: Optional[str]) -> str:
        if v is None:
            return DEFAULT_VOICE
        v = v.strip()
        if v not in AVAILABLE_VOICES:
            raise ValueError(f"Invalid voice '{v}'. Allowed: {', '.join(AVAILABLE_VOICES.keys())}")
        return v

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: Optional[str]) -> str:
        if v is None:
            return "wav"
        v = v.strip().lower()
        allowed = ['wav', 'mp3', 'ogg']
        if v not in allowed:
            raise ValueError(f"Invalid format '{v}'. Allowed: {', '.join(allowed)}")
        return v


class BatchTTSRequest(BaseModel):
    """Batch TTS request for multiple texts."""
    items: List[TTSRequest] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of TTS requests (max 10)"
    )


class BatchTTSResultItem(BaseModel):
    """Individual result item in batch TTS response."""
    text: str = Field(description="Original text that was processed")
    audio_base64: Optional[str] = Field(
        default=None,
        description="Base64-encoded audio data (null if error occurred)"
    )
    format: str = Field(description="Audio format (wav, mp3, ogg)")
    cached: bool = Field(description="Whether result was served from cache")
    size_bytes: int = Field(description="Size of audio data in bytes (0 if error)")
    generation_ms: Optional[float] = Field(
        default=None,
        description="Generation time in milliseconds (null if cached or error)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if generation failed (null if successful)"
    )


class BatchTTSResponse(BaseModel):
    """Response for batch TTS request."""
    results: List[BatchTTSResultItem] = Field(description="List of results with audio data")
    total_duration_ms: float = Field(description="Total generation time")
    cached_count: int = Field(description="Number of results from cache")


@router.get("/voices")
async def list_voices():
    """List available voices."""
    return {"voices": AVAILABLE_VOICES, "default": DEFAULT_VOICE}


@router.post("/tts/announce")
async def announce_text(request: TTSRequest, background_tasks: BackgroundTasks):
    """Generate TTS and optionally broadcast via WebSocket."""
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    async def generate_tts():
        voice = request.voice or DEFAULT_VOICE
        speed = request.speed or 1.0
        output_format = request.format or "wav"
        use_cache = request.use_cache if request.use_cache is not None else True

        # Check cache first
        cached_result = None
        if use_cache:
            cached_result = tts_cache.get(request.text, voice, speed, format=output_format)

        if cached_result:
            audio_bytes, sample_rate = cached_result
            logger.info("TTS cache hit", extra={
                'text_preview': request.text[:50],
                'voice': voice,
                'cached': True
            })
            metrics.inc_tts_generated(cached=True, bytes_size=len(audio_bytes))
            return audio_bytes, output_format
        else:
            pipe = load_pipeline()

            logger.info("Generating TTS", extra={
                'text_preview': request.text[:50],
                'voice': voice,
                'speed': speed
            })
            start_time = time.time()

            generator = pipe(
                request.text,
                voice=voice,
                speed=speed
            )

            audio_chunks = []
            for i, (gs, ps, audio) in enumerate(generator):
                audio_chunks.append(audio)

            if len(audio_chunks) > 1:
                full_audio = np.concatenate(audio_chunks)
            else:
                full_audio = audio_chunks[0]

            gen_time = time.time() - start_time
            gen_time_ms = round(gen_time * 1000, 1)

            audio_bytes, mime_type = audio_encoder.encode(
                full_audio, 24000, output_format
            )

            logger.info("TTS generated", extra={
                'duration_ms': gen_time_ms,
                'text_length': len(request.text),
                'format': output_format,
                'size_kb': round(len(audio_bytes) / 1024, 1)
            })

            metrics.observe_tts_latency(gen_time, len(request.text))
            metrics.inc_tts_generated(cached=False, bytes_size=len(audio_bytes))

            if use_cache:
                tts_cache.put(
                    request.text, voice, audio_bytes, 24000,
                    speed=speed, format=output_format,
                    generation_time_ms=gen_time_ms
                )

            return audio_bytes, output_format

    try:
        audio_bytes, output_format = await request_queue.execute(generate_tts)

        # Broadcast to WebSocket clients (thread-safe)
        async with _websocket_lock:
            clients_to_notify = list(websocket_clients)
        
        if clients_to_notify:
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            message = {
                "type": "audio",
                "audio": audio_b64,
                "text": request.text,
                "sample_rate": 24000
            }
            
            disconnected_clients = []
            for client in clients_to_notify:
                try:
                    await client.send_json(message)
                except Exception as e:
                    logger.debug("Failed to send to WebSocket client", extra={'error': str(e)})
                    disconnected_clients.append(client)
            
            # Remove disconnected clients (thread-safe)
            if disconnected_clients:
                async with _websocket_lock:
                    for client in disconnected_clients:
                        websocket_clients.discard(client)

        format_info = audio_encoder.FORMATS.get(output_format, audio_encoder.FORMATS['wav'])
        return Response(
            content=audio_bytes,
            media_type=format_info['mime_type'],
            headers={
                "Content-Disposition": f"attachment; filename=speech{format_info['extension']}"
            }
        )

    except Exception as e:
        logger.exception("TTS generation failed", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/tts")
async def websocket_tts(websocket: WebSocket):
    """WebSocket endpoint for TTS streaming."""
    await websocket.accept()
    
    # Thread-safe client addition
    async with _websocket_lock:
        websocket_clients.add(websocket)
        client_count = len(websocket_clients)
    
    logger.info("WebSocket client connected", extra={'ws_clients': client_count})

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("WebSocket error", extra={'error': str(e)})
    finally:
        # Thread-safe client removal
        async with _websocket_lock:
            websocket_clients.discard(websocket)
            client_count = len(websocket_clients)
        logger.info("WebSocket client disconnected", extra={'ws_clients': client_count})


@router.post("/tts/batch", response_model=BatchTTSResponse)
async def batch_tts(request: BatchTTSRequest):
    """Process multiple TTS requests in a single call with per-item error handling."""
    start_time = time.time()
    results = []
    cached_count = 0
    error_count = 0

    pipe = load_pipeline()

    for item in request.items:
        try:
            voice = item.voice or DEFAULT_VOICE
            speed = item.speed or 1.0
            output_format = item.format or "wav"
            use_cache = item.use_cache if item.use_cache is not None else True

            cached_result = None
            if use_cache:
                cached_result = tts_cache.get(item.text, voice, speed, format=output_format)

            if cached_result:
                audio_bytes, sample_rate = cached_result
                cached_count += 1
                results.append(BatchTTSResultItem(
                    text=item.text,
                    audio_base64=base64.b64encode(audio_bytes).decode("utf-8"),
                    format=output_format,
                    cached=True,
                    size_bytes=len(audio_bytes),
                    error=None
                ))
            else:
                item_start = time.time()

                try:
                    generator = pipe(item.text, voice=voice, speed=speed)
                    audio_chunks = []
                    for i, (gs, ps, audio) in enumerate(generator):
                        audio_chunks.append(audio)

                    if len(audio_chunks) > 1:
                        full_audio = np.concatenate(audio_chunks)
                    else:
                        full_audio = audio_chunks[0]

                    audio_bytes, mime_type = audio_encoder.encode(
                        full_audio, 24000, output_format
                    )

                    gen_time_ms = round((time.time() - item_start) * 1000, 1)

                    if use_cache:
                        tts_cache.put(
                            item.text, voice, audio_bytes, 24000,
                            speed=speed, format=output_format,
                            generation_time_ms=gen_time_ms
                        )

                    results.append(BatchTTSResultItem(
                        text=item.text,
                        audio_base64=base64.b64encode(audio_bytes).decode("utf-8"),
                        format=output_format,
                        cached=False,
                        size_bytes=len(audio_bytes),
                        generation_ms=gen_time_ms,
                        error=None
                    ))
                except Exception as gen_error:
                    error_count += 1
                    error_msg = str(gen_error)
                    logger.error(
                        "Batch TTS item generation failed",
                        extra={
                            'text_preview': item.text[:50],
                            'voice': voice,
                            'error': error_msg
                        }
                    )
                    results.append(BatchTTSResultItem(
                        text=item.text,
                        audio_base64=None,
                        format=output_format,
                        cached=False,
                        size_bytes=0,
                        generation_ms=None,
                        error=error_msg
                    ))

        except Exception as item_error:
            error_count += 1
            error_msg = str(item_error)
            logger.error(
                "Batch TTS item processing failed",
                extra={
                    'text_preview': item.text[:50] if hasattr(item, 'text') else 'unknown',
                    'error': error_msg
                }
            )
            results.append(BatchTTSResultItem(
                text=getattr(item, 'text', 'unknown'),
                audio_base64=None,
                format=getattr(item, 'format', 'wav'),
                cached=False,
                size_bytes=0,
                generation_ms=None,
                error=error_msg
            ))

    total_time = round((time.time() - start_time) * 1000, 1)

    logger.info("Batch TTS completed", extra={
        'items': len(request.items),
        'cached': cached_count,
        'errors': error_count,
        'total_ms': total_time
    })

    return BatchTTSResponse(
        results=results,
        total_duration_ms=total_time,
        cached_count=cached_count
    )
