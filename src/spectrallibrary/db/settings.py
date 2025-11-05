"""Database configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_APP_DIR = Path.home() / ".spectrallibrary"


@dataclass(slots=True)
class DatabaseSettings:
    """Static configuration for database connections."""

    app_dir: Path = DEFAULT_APP_DIR
    database_path: Optional[Path] = None
    database_url: Optional[str] = None
    echo: bool = False


def get_database_settings() -> DatabaseSettings:
    """Return database settings.

    For now this returns defaults; in the future this will read from config files
    or environment variables.
    """

    return DatabaseSettings()
