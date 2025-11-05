"""Session utilities for working with the database."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .engine import get_engine

SessionLocal = sessionmaker(autoflush=False, autocommit=False, expire_on_commit=False)
SessionLocal.configure(bind=get_engine())


def configure_session(bind: Engine) -> None:
    """Reconfigure the session factory to use a different engine."""

    SessionLocal.configure(bind=bind)


@contextmanager
def get_session() -> Iterator[Session]:
    """Yield a transactional session and ensure cleanup."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
