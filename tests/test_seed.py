from __future__ import annotations

import pytest
from sqlalchemy import create_engine, func, select

from spectrallibrary.db.base import Base
from spectrallibrary.db.engine import get_engine
from spectrallibrary.db.models import Material
from spectrallibrary.db.session import configure_session, get_session
from spectrallibrary.seed import seed_demo_data


@pytest.fixture(autouse=True)
def _use_in_memory_database():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    original_engine = get_engine()
    configure_session(engine)
    try:
        yield
    finally:
        configure_session(original_engine)
        engine.dispose()


def _material_count() -> int:
    with get_session() as session:
        return session.execute(select(func.count()).select_from(Material)).scalar_one()


def test_seed_demo_data_populates_materials_when_empty():
    created = seed_demo_data()
    assert created == 3
    assert _material_count() == 3

    created_again = seed_demo_data()
    assert created_again == 0
    assert _material_count() == 3


def test_seed_demo_data_force_replaces_existing_records():
    seed_demo_data()
    assert _material_count() == 3

    created = seed_demo_data(force=True)
    assert created == 3
    assert _material_count() == 3
