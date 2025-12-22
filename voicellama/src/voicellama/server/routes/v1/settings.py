"""Settings management endpoints for API v1."""

# Re-export v1 routes (for now, same as current routes)
from voicellama.server.routes import settings

router = settings.router

