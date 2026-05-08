# ============================================================
#  Centralized Configuration
#  Loads settings from .env and provides typed access.
# ============================================================

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root ──────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Immutable application settings loaded from environment variables."""

    # LLM / NVIDIA API
    openai_api_key: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", "")
    )
    openai_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1"
        )
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "openai/gpt-oss-120b")
    )

    # Application
    max_upload_size_mb: int = field(
        default_factory=lambda: int(os.getenv("MAX_UPLOAD_SIZE_MB", "200"))
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "50000"))
    )

    # Paths
    upload_dir: Path = field(
        default_factory=lambda: _PROJECT_ROOT / "data" / "uploads"
    )

    def __post_init__(self) -> None:
        """Ensure the upload directory exists."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)


# ── Singleton ────────────────────────────────────────────────
_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the global Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
