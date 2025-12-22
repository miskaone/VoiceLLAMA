"""UI page routes."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


def get_static_dir() -> Path:
    """Get the static files directory."""
    return Path(__file__).parent.parent.parent / "static"


@router.get("/", response_class=HTMLResponse)
async def settings_page():
    """Serve the settings page."""
    settings_file = get_static_dir() / "settings.html"
    if settings_file.exists():
        return HTMLResponse(content=settings_file.read_text())
    return HTMLResponse(
        content="<h1>VoiceLLAMA</h1><p>Settings page not found. Static files may not be installed.</p>",
        status_code=404
    )


@router.get("/avatar", response_class=HTMLResponse)
async def avatar_page():
    """Serve the avatar page."""
    avatar_file = get_static_dir() / "avatar.html"
    if avatar_file.exists():
        return HTMLResponse(content=avatar_file.read_text())
    return HTMLResponse(content="<h1>Avatar file not found</h1>", status_code=404)


