"""Configuration management for VoiceLLAMA.

Configuration priority (highest to lowest):
1. CLI arguments
2. Environment variables
3. voicellama.toml config file
4. Built-in defaults
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


@dataclass
class ServerConfig:
    """Server configuration."""
    port: int = 8333
    host: str = "0.0.0.0"
    log_level: str = "INFO"
    log_format: str = "dev"  # "dev" or "json"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    cors_allow_all: bool = False
    cors_origins: List[str] = field(default_factory=list)
    startup_sound: bool = False  # Play sound when server starts


@dataclass
class TTSConfig:
    """TTS configuration."""
    default_voice: str = "af_heart"
    default_speed: float = 1.0
    enabled: bool = True
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds


@dataclass
class AvatarConfig:
    """Avatar configuration."""
    enabled: bool = False


@dataclass
class ChatterConfig:
    """Chatter level configuration."""
    level: str = "sparse"  # sparse, summary, verbose, custom
    question: bool = True
    summary: bool = False
    detail: bool = False


@dataclass
class Config:
    """Main configuration container."""
    server: ServerConfig = field(default_factory=ServerConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    avatar: AvatarConfig = field(default_factory=AvatarConfig)
    chatter: ChatterConfig = field(default_factory=ChatterConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from file and environment.

        Args:
            config_path: Optional path to voicellama.toml

        Returns:
            Config instance with merged settings
        """
        config = cls()

        # Try to load from config file
        if config_path:
            config._load_from_file(Path(config_path))
        else:
            # Look for voicellama.toml in current directory
            default_path = Path("voicellama.toml")
            if default_path.exists():
                config._load_from_file(default_path)

        # Override with environment variables
        config._load_from_env()

        return config

    def _load_from_file(self, path: Path) -> None:
        """Load configuration from TOML file."""
        if not path.exists():
            return

        if tomllib is None:
            print(f"Warning: tomllib not available, skipping config file {path}")
            return

        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Server config
        if "server" in data:
            server = data["server"]
            if "port" in server:
                self.server.port = server["port"]
            if "host" in server:
                self.server.host = server["host"]
            if "log_level" in server:
                self.server.log_level = server["log_level"]
            if "log_format" in server:
                self.server.log_format = server["log_format"]
            if "rate_limit_requests" in server:
                self.server.rate_limit_requests = server["rate_limit_requests"]
            if "rate_limit_window" in server:
                self.server.rate_limit_window = server["rate_limit_window"]
            if "cors_allow_all" in server:
                self.server.cors_allow_all = server["cors_allow_all"]
            if "cors_origins" in server:
                self.server.cors_origins = server["cors_origins"]
            if "startup_sound" in server:
                self.server.startup_sound = server["startup_sound"]

        # TTS config
        if "tts" in data:
            tts = data["tts"]
            if "default_voice" in tts:
                self.tts.default_voice = tts["default_voice"]
            if "default_speed" in tts:
                self.tts.default_speed = tts["default_speed"]
            if "enabled" in tts:
                self.tts.enabled = tts["enabled"]
            if "cache_enabled" in tts:
                self.tts.cache_enabled = tts["cache_enabled"]
            if "cache_ttl" in tts:
                self.tts.cache_ttl = tts["cache_ttl"]

        # Avatar config
        if "avatar" in data:
            if "enabled" in data["avatar"]:
                self.avatar.enabled = data["avatar"]["enabled"]

        # Chatter config
        if "chatter" in data:
            chatter = data["chatter"]
            if "level" in chatter:
                self.chatter.level = chatter["level"]
            if "question" in chatter:
                self.chatter.question = chatter["question"]
            if "summary" in chatter:
                self.chatter.summary = chatter["summary"]
            if "detail" in chatter:
                self.chatter.detail = chatter["detail"]

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Server config
        if port := os.getenv("PORT"):
            self.server.port = int(port)
        if host := os.getenv("HOST"):
            self.server.host = host
        if log_level := os.getenv("LOG_LEVEL"):
            self.server.log_level = log_level
        if log_format := os.getenv("LOG_FORMAT"):
            self.server.log_format = log_format
        if rate_limit := os.getenv("RATE_LIMIT_REQUESTS"):
            self.server.rate_limit_requests = int(rate_limit)
        if rate_window := os.getenv("RATE_LIMIT_WINDOW"):
            self.server.rate_limit_window = int(rate_window)
        if cors_all := os.getenv("CORS_ALLOW_ALL"):
            self.server.cors_allow_all = cors_all.lower() in ("true", "1", "yes")
        if cors_origins := os.getenv("CORS_ORIGINS"):
            self.server.cors_origins = [o.strip() for o in cors_origins.split(",")]
        if startup_sound := os.getenv("STARTUP_SOUND"):
            self.server.startup_sound = startup_sound.lower() in ("true", "1", "yes")

        # TTS config
        if voice := os.getenv("DEFAULT_VOICE"):
            self.tts.default_voice = voice
        if speed := os.getenv("DEFAULT_SPEED"):
            self.tts.default_speed = float(speed)
