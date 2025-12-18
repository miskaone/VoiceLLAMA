"""UI page routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

router = APIRouter(tags=["ui"])


def get_static_dir() -> Path:
    """Get the static files directory."""
    return Path(__file__).parent.parent / "static"


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


@router.get("/images/{filename}")
async def serve_image(filename: str):
    """Serve images from the images folder with path traversal protection."""
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'}
    ext = Path(filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")

    images_dir = get_static_dir() / "images"
    image_path = images_dir / filename

    try:
        resolved = image_path.resolve()
        if not str(resolved).startswith(str(images_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid path")
    except (OSError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid path")

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(resolved)
