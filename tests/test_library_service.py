from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine

from spectrallibrary.db.base import Base
from spectrallibrary.db.engine import get_engine
from spectrallibrary.db.models import Material, Spectrum
from spectrallibrary.db.session import configure_session, get_session
from spectrallibrary.services import LibraryBrowserService


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


def test_fetch_library_tree_empty_database_returns_no_libraries():
    service = LibraryBrowserService()

    libraries = service.fetch_library_tree()

    assert libraries == ()


def test_fetch_library_tree_groups_materials_and_spectra():
    with get_session() as session:
        basalt = Material(
            library_name="Global Reference",
            material_name="Basalt Collection",
            category="Igneous",
        )
        spectrum_a = Spectrum(
            material=basalt,
            source="ASD FieldSpec 4",
            wavelength_unit="nm",
            reflectance_unit="fraction",
            acquisition_date=date(2024, 3, 14),
            quality_status="complete",
        )
        spectrum_b = Spectrum(
            material=basalt,
            source="ASD FieldSpec 4",
            wavelength_unit="nm",
            reflectance_unit="fraction",
            acquisition_date=None,
            quality_status="incomplete",
        )
        session.add_all([basalt, spectrum_a, spectrum_b])

        hematite = Material(
            library_name="Global Reference",
            material_name="Hematite",
            category="Oxide",
        )
        spectrum_c = Spectrum(
            material=hematite,
            source="ASD TerraSpec",
            wavelength_unit="nm",
            reflectance_unit="fraction",
            acquisition_date=date(2024, 5, 9),
            quality_status="complete",
        )
        session.add_all([hematite, spectrum_c])

        ice = Material(
            library_name="Field Campaign 2024",
            material_name="Ice Sample",
            category="Cryogenic",
        )
        session.add(ice)

    service = LibraryBrowserService()
    libraries = service.fetch_library_tree()

    assert len(libraries) == 2
    global_ref = next(lib for lib in libraries if lib.name == "Global Reference")
    assert len(global_ref.materials) == 2
    basalt_node = next(mat for mat in global_ref.materials if mat.name == "Basalt Collection")
    assert len(basalt_node.spectra) == 2
    first_label = basalt_node.spectra[0].label
    assert "ASD FieldSpec 4" in first_label
    assert "2024-03-14" in first_label

    field_campaign = next(lib for lib in libraries if lib.name == "Field Campaign 2024")
    assert len(field_campaign.materials) == 1
    assert field_campaign.materials[0].spectra == ()
