"""Settings management endpoints."""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

router = APIRouter(tags=["settings"])

# Settings file path
SETTINGS_FILE = Path.cwd() / "voicellama_settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "engine": "kokoro",
    "voice": "af_heart",
    "speed": 1.0,
    "enabled": True,
    "avatar_enabled": False,
    "chatter_level": "sparse",
    "custom_states": {
        "question": True,
        "summary": False,
        "detail": False
    }
}

# Context window state
context_state = {
    "used": 0,
    "total": 200000,
    "percentage": 0
}


class CustomStates(BaseModel):
    """Custom chatter level states."""
    question: bool = True
    summary: bool = False
    detail: bool = False


class SettingsUpdate(BaseModel):
    """Settings update with validation."""
    engine: Optional[str] = Field(default=None, description="TTS engine")
    voice: Optional[str] = Field(default=None, description="Voice name")
    speed: Optional[float] = Field(default=None, ge=0.25, le=3.0, description="Speech speed")
    enabled: Optional[bool] = Field(default=None, description="TTS enabled")
    avatar_enabled: Optional[bool] = Field(default=None, description="Avatar enabled")
    chatter_level: Optional[str] = Field(default=None, description="Chatter level")
    custom_states: Optional[CustomStates] = Field(default=None, description="Custom states")

    @field_validator('engine')
    @classmethod
    def validate_engine(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = ['kokoro']
        if v not in allowed:
            raise ValueError(f"Engine must be one of: {', '.join(allowed)}")
        return v

    @field_validator('voice')
    @classmethod
    def validate_voice(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if len(v) > 100:
            raise ValueError("Voice name too long (max 100 characters)")
        return v

    @field_validator('chatter_level')
    @classmethod
    def validate_chatter_level(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        allowed = ['sparse', 'summary', 'verbose', 'custom']
        if v not in allowed:
            raise ValueError(f"Chatter level must be one of: {', '.join(allowed)}")
        return v


def load_settings() -> dict:
    """Load settings from file."""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE) as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Save settings to file."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


@router.get("/settings")
async def get_settings():
    """Get current TTS settings."""
    return load_settings()


@router.post("/settings")
async def update_settings(settings: SettingsUpdate):
    """Update TTS settings."""
    current = load_settings()
    update_data = settings.model_dump(exclude_none=True)

    if 'custom_states' in update_data and update_data['custom_states']:
        current['custom_states'] = {**current.get('custom_states', {}), **update_data['custom_states']}
        del update_data['custom_states']

    current.update(update_data)
    save_settings(current)
    return current


@router.get("/context")
async def get_context():
    """Get current context window state."""
    return context_state


@router.post("/context")
async def update_context(data: dict):
    """Update context window state."""
    global context_state
    if "used" in data:
        context_state["used"] = data["used"]
    if "total" in data:
        context_state["total"] = data["total"]
    if "percentage" in data:
        context_state["percentage"] = data["percentage"]
    elif context_state["total"] > 0:
        context_state["percentage"] = round(context_state["used"] / context_state["total"] * 100, 1)

    return context_state
