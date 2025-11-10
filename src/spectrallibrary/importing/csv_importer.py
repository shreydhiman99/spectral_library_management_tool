"""CSV importer for spectral records."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .base import ImportContext, ImportResult, SpectrumRecord
from .registry import register_importer


_REQUIRED_COLUMNS: tuple[str, ...] = (
    "library_name",
    "material_name",
    "category",
    "source",
    "wavelength_unit",
    "reflectance_unit",
    "wavelengths",
    "reflectance",
)


@dataclass(slots=True)
class CsvSpectrumImporter:
    """Parse spectral records from CSV files with semicolon-delimited series."""

    formats: Sequence[str] = ("csv",)

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".csv"

    def load(self, path: Path, *, context: ImportContext | None = None) -> ImportResult:
        records: list[SpectrumRecord] = []
        warnings: list[str] = []

        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self._ensure_required_columns(reader.fieldnames)

            for row_number, row in enumerate(reader, start=2):  # header is row 1
                try:
                    record = self._build_record(row, context=context)
                except ValueError as exc:
                    warnings.append(f"Row {row_number}: {exc}")
                    continue

                try:
                    record.validate()
                except ValueError as exc:
                    warnings.append(f"Row {row_number}: {exc}")
                    continue

                records.append(record)

        return ImportResult(records=records, warnings=warnings)

    # ------------------------------------------------------------------
    # Helpers

    def _ensure_required_columns(self, fieldnames: Sequence[str] | None) -> None:
        if not fieldnames:
            raise ValueError("CSV file is missing a header row")

        missing = [name for name in _REQUIRED_COLUMNS if name not in fieldnames]
        if missing:
            raise ValueError(f"CSV file missing required columns: {', '.join(missing)}")

    def _build_record(self, row: Mapping[str, str], *, context: ImportContext | None) -> SpectrumRecord:
        override_library = context.target_library if context else None
        library_name = (override_library or row.get("library_name", "")).strip()
        if not library_name:
            raise ValueError("library_name is required")

        material_name = row.get("material_name", "").strip()
        category = row.get("category", "").strip()
        source = row.get("source", "").strip()
        wavelength_unit = row.get("wavelength_unit", "").strip()
        reflectance_unit = row.get("reflectance_unit", "").strip()

        if not material_name or not category or not source:
            raise ValueError("material_name, category, and source are required")
        if not wavelength_unit or not reflectance_unit:
            raise ValueError("wavelength_unit and reflectance_unit are required")

        wavelengths = _parse_float_series(row.get("wavelengths", ""))
        reflectance = _parse_float_series(row.get("reflectance", ""))

        location = row.get("location") or None
        comments = row.get("comments") or None
        acquisition_date = _parse_date(row.get("acquisition_date"))
        tags = _parse_tags(row.get("tags"))

        metadata = {
            key: value
            for key, value in row.items()
            if key not in _REQUIRED_COLUMNS and key not in {"location", "comments", "acquisition_date", "tags"}
            and value not in (None, "")
        }

        return SpectrumRecord(
            library_name=library_name,
            material_name=material_name,
            category=category,
            source=source,
            wavelength_unit=wavelength_unit,
            reflectance_unit=reflectance_unit,
            wavelengths=wavelengths,
            reflectance=reflectance,
            location=location,
            acquisition_date=acquisition_date,
            comments=comments,
            metadata=metadata,
            tags=tags,
        )


def _parse_float_series(raw: str) -> Sequence[float]:
    values = [value.strip() for value in raw.split(";") if value and value.strip()]
    if not values:
        raise ValueError("series must contain at least one value")
    return [float(value) for value in values]


def _parse_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw.strip())
    except ValueError as exc:  # pragma: no cover - defensive branch for invalid dates
        raise ValueError(f"invalid acquisition_date: {raw}") from exc


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [token.strip() for token in raw.split(";") if token.strip()]


register_importer(CsvSpectrumImporter())
