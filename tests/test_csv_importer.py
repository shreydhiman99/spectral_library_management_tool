from __future__ import annotations

import io
from pathlib import Path

import pytest

from spectrallibrary.importing.csv_importer import CsvSpectrumImporter
from spectrallibrary.importing.base import ImportContext


@pytest.fixture
def csv_importer() -> CsvSpectrumImporter:
    return CsvSpectrumImporter()


def _write_temp_csv(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "sample.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_importer_parses_valid_rows(tmp_path: Path, csv_importer: CsvSpectrumImporter) -> None:
    content = """library_name,material_name,category,source,wavelength_unit,reflectance_unit,wavelengths,reflectance,tags\n"""
    content += "Global Reference,Basalt-01,Igneous,ASD, nm, fraction,400;500,0.1;0.2,peak-a;peak-b\n"
    path = _write_temp_csv(tmp_path, content)

    result = csv_importer.load(path)

    assert len(result.records) == 1
    record = result.records[0]
    assert record.library_name == "Global Reference"
    assert record.tags == ["peak-a", "peak-b"]


def test_importer_respects_context_override(tmp_path: Path, csv_importer: CsvSpectrumImporter) -> None:
    content = """library_name,material_name,category,source,wavelength_unit,reflectance_unit,wavelengths,reflectance\n"""
    content += "Original,Material,Igneous,ASD,nm,fraction,400;500,0.1;0.2\n"
    path = _write_temp_csv(tmp_path, content)

    result = csv_importer.load(path, context=ImportContext(target_library="Override"))
    assert result.records[0].library_name == "Override"


def test_importer_collects_row_warnings(tmp_path: Path, csv_importer: CsvSpectrumImporter) -> None:
    content = """library_name,material_name,category,source,wavelength_unit,reflectance_unit,wavelengths,reflectance\n"""
    content += ",Material,Igneous,ASD,nm,fraction,400;500,0.1;0.2\n"  # missing library
    path = _write_temp_csv(tmp_path, content)

    result = csv_importer.load(path)

    assert result.records == []
    assert result.warnings


def test_importer_requires_header(tmp_path: Path, csv_importer: CsvSpectrumImporter) -> None:
    path = _write_temp_csv(tmp_path, "")
    with pytest.raises(ValueError):
        csv_importer.load(path)


def test_importer_rejects_missing_columns(tmp_path: Path, csv_importer: CsvSpectrumImporter) -> None:
    content = """library_name,material_name\nfoo,bar\n"""
    path = _write_temp_csv(tmp_path, content)

    with pytest.raises(ValueError):
        csv_importer.load(path)
