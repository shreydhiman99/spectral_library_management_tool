from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select

from spectrallibrary.db.base import Base
from spectrallibrary.db.engine import get_engine
from spectrallibrary.db.models import Material, Spectrum, Tag
from spectrallibrary.db.session import configure_session, get_session
from spectrallibrary.importing import importer_registry
from spectrallibrary.services import ImportService


@pytest.fixture(autouse=True)
def _use_in_memory_database(tmp_path):
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    original_engine = get_engine()
    configure_session(engine)
    try:
        yield
    finally:
        configure_session(original_engine)
        engine.dispose()


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    path = tmp_path / "sample.csv"
    path.write_text(
        """library_name,material_name,category,source,wavelength_unit,reflectance_unit,wavelengths,reflectance,acquisition_date\n"""
        "Global Reference,Basalt-01,Igneous,ASD FieldSpec 4,nm,fraction,400;401,0.11;0.12,2024-03-14\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def invalid_csv(tmp_path: Path) -> Path:
    path = tmp_path / "invalid.csv"
    path.write_text(
        """library_name,material_name,category,source,wavelength_unit,reflectance_unit,wavelengths,reflectance\n"""
        "Global Reference,Basalt-01,Igneous,ASD FieldSpec 4,nm,fraction,,0.11;0.12\n",
        encoding="utf-8",
    )
    return path


def test_import_service_persists_records(sample_csv: Path) -> None:
    service = ImportService()

    summary = service.import_path(sample_csv)

    assert summary.created_materials == 1
    assert summary.created_spectra == 1
    assert not summary.warnings

    with get_session() as session:
        material = session.execute(select(Material)).scalar_one()
        assert material.library_name == "Global Reference"

        spectrum = session.execute(select(Spectrum)).scalar_one()
        assert spectrum.acquisition_date == date(2024, 3, 14)


def test_import_service_handles_duplicate_material(sample_csv: Path) -> None:
    service = ImportService()

    service.import_path(sample_csv)
    summary = service.import_path(sample_csv)

    assert summary.created_materials == 0
    assert summary.created_spectra == 1

    with get_session() as session:
        material_count = session.execute(select(func.count()).select_from(Material)).scalar_one()
        spectrum_count = session.execute(select(func.count()).select_from(Spectrum)).scalar_one()

    assert material_count == 1
    assert spectrum_count == 2


def test_import_service_reports_progress(sample_csv: Path) -> None:
    service = ImportService()
    calls: list[tuple[int, int]] = []

    def progress(processed: int, total: int) -> None:
        calls.append((processed, total))

    service.import_path(sample_csv, progress_callback=progress)

    assert calls, "progress callback should have been invoked"
    assert calls[0] == (0, 1)
    assert calls[-1] == (1, 1)


def test_import_service_reuses_existing_tags(tmp_path: Path) -> None:
    csv_path = tmp_path / "with_tags.csv"
    csv_path.write_text(
        """library_name,material_name,category,source,wavelength_unit,reflectance_unit,wavelengths,reflectance,tags
Campaign,Basalt A,Igneous,ASD FieldSpec 4,nm,ratio,400;401,0.1;0.2,basalt;field
Campaign,Basalt B,Igneous,ASD FieldSpec 4,nm,ratio,400;401,0.2;0.3,basalt;field
""",
        encoding="utf-8",
    )

    service = ImportService()
    summary = service.import_path(csv_path)

    assert summary.created_materials == 2
    assert summary.created_spectra == 2
    assert not summary.warnings

    with get_session() as session:
        tag_count = session.execute(select(func.count()).select_from(Tag)).scalar_one()
    assert tag_count == 2


def test_importer_registry_returns_empty_result_with_warnings(invalid_csv: Path) -> None:
    result = importer_registry.import_file(invalid_csv)

    assert result.records == []
    assert result.warnings, "Warnings should be reported for invalid rows"


def test_import_service_handles_warning_only_import(invalid_csv: Path) -> None:
    service = ImportService()

    summary = service.import_path(invalid_csv)

    assert summary.created_materials == 0
    assert summary.created_spectra == 0
    assert summary.warnings, "Warnings should be propagated to the summary"
