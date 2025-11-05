"""Engine creation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine as _create_engine
from sqlalchemy.engine import Engine

from .settings import DatabaseSettings, get_database_settings

_ENGINE_CACHE: dict[str, Engine] = {}


def _build_database_url(settings: DatabaseSettings) -> str:
    if settings.database_url:
        return settings.database_url
    # default to application data directory / spectral-library.db
    path = Path(settings.database_path or (settings.app_dir / "spectral-library.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


def create_engine(settings: Optional[DatabaseSettings] = None, *, echo: bool | None = None) -> Engine:
    """Create a new SQLAlchemy engine.

    Args:
        settings: Optional application database settings.
        echo: Override for SQLAlchemy echo flag; defaults to settings.echo.
    """

    settings = settings or get_database_settings()
    database_url = _build_database_url(settings)
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {}

    engine = _create_engine(
        database_url,
        echo=settings.echo if echo is None else echo,
        future=True,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    return engine


def get_engine(cache_key: str = "default") -> Engine:
    """Get (and cache) an engine instance keyed by cache key."""

    if cache_key not in _ENGINE_CACHE:
        _ENGINE_CACHE[cache_key] = create_engine()
    return _ENGINE_CACHE[cache_key]


def configure_engine(engine: Engine, cache_key: str = "default") -> None:
    """Override the cached engine (useful for testing)."""

    _ENGINE_CACHE[cache_key] = engine
    if cache_key == "default":
        # Avoid circular import at module level
        from .session import configure_session

        configure_session(engine)
