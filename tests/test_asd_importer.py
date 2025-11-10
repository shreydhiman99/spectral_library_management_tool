from __future__ import annotations

from pathlib import Path

import pytest

from spectrallibrary.importing import ImportContext, importer_registry


@pytest.fixture
def asd_fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "asd" / "sample_reflectance.sig"


@pytest.fixture
def asd_radiance_path() -> Path:
    return Path(__file__).parent / "fixtures" / "asd" / "sample_radiance.sig"


def test_asd_importer_detects_file(asd_fixture_path: Path) -> None:
    importer = None
    for candidate in importer_registry.available_importers():
        if candidate.can_handle(asd_fixture_path):
            importer = candidate
            break
    assert importer is not None, "ASD importer should handle .sig files"


def test_asd_importer_parses_reflectance(asd_fixture_path: Path) -> None:
    result = importer_registry.import_file(asd_fixture_path, context=ImportContext(target_library="Campaign"))

    assert len(result.records) == 1
    record = result.records[0]

    assert record.library_name == "Campaign"
    assert record.material_name == "Basalt-01"
    assert record.category == "Igneous"
    assert record.source.startswith("ASD FieldSpec 4")
    assert record.wavelength_unit == "nm"
    assert record.reflectance_unit == "ratio"
    assert record.wavelengths == [350.0, 351.0, 352.0]
    assert record.reflectance == [0.11, 0.12, 0.13]
    assert "asd" in record.tags

    assert not result.warnings


def test_asd_importer_handles_radiance_only(asd_radiance_path: Path) -> None:
    result = importer_registry.import_file(asd_radiance_path)

    assert len(result.records) == 1
    record = result.records[0]

    assert record.material_name == "Quartz-01"
    assert record.reflectance_unit == "radiance"
    assert record.reflectance == [1.01, 0.99, 0.97]
    assert result.warnings
    assert any("Reflectance column missing" in warning for warning in result.warnings)
