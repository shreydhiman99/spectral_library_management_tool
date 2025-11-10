"""Importer for ASD ASCII/SIG spectral files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .base import ImportContext, ImportResult, SpectrumRecord
from .registry import register_importer


@dataclass(slots=True)
class AsdAsciiImporter:
    """Parse ASD ASCII exports (SIG/TXT) into SpectrumRecord instances."""

    formats: tuple[str, ...] = ("sig", "txt")

    def can_handle(self, path: Path) -> bool:
        suffix = path.suffix.lower()
        if suffix not in {".sig", ".txt"}:
            return False
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                head = "\n".join(handle.readline().strip() for _ in range(5))
        except OSError:
            return False
        lowered = head.lower()
        return any(token in lowered for token in ("asd", "fieldspec", "spectravista"))

    def load(self, path: Path, *, context: ImportContext | None = None) -> ImportResult:
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError as exc:
            raise ValueError(f"Unable to read ASD file: {exc}") from exc

        metadata, column_names, data_lines = _split_sections(lines)
        if not column_names:
            raise ValueError("Unable to locate ASD data columns (expected a header row containing 'Wavelength').")

        parse_result = _parse_numeric_rows(column_names, data_lines)
        wavelengths = parse_result["wavelengths"]
        reflectance = parse_result["reflectance"]
        warnings = parse_result["warnings"]
        inferred_units = parse_result["reflectance_unit"]

        override_library = context.target_library if context else None
        library_name = override_library or metadata.get("Library") or "ASD Imports"
        material_name = (
            (context.extra_options or {}).get("material_name")
            if context and context.extra_options
            else None
        ) or metadata.get("Sample") or metadata.get("Target") or path.stem
        category = metadata.get("Category") or "Field"
        instrument = metadata.get("Instrument") or metadata.get("Device") or "ASD Spectrometer"
        source = instrument
        if integration := metadata.get("Integration Time"):
            source = f"{instrument} (Integration {integration})"

        reflectance_unit = inferred_units
        reflectance_values = reflectance
        if not reflectance_values:
            radiance = parse_result.get("radiance")
            if radiance:
                reflectance_values = radiance
                reflectance_unit = "radiance"
                warnings.append("Reflectance column missing - radiance values stored instead.")
            else:
                raise ValueError("ASD file did not contain reflectance or radiance data columns.")

        comments = metadata.get("Comments")

        record = SpectrumRecord(
            library_name=library_name,
            material_name=material_name,
            category=category,
            source=source,
            wavelength_unit=metadata.get("Wavelength Unit", "nm"),
            reflectance_unit=reflectance_unit,
            wavelengths=wavelengths,
            reflectance=reflectance_values,
            location=metadata.get("Location"),
            acquisition_date=None,
            comments=comments,
            metadata={k: v for k, v in metadata.items() if k not in {"Library", "Sample", "Target", "Category", "Instrument", "Device", "Comments"}},
            tags=_build_tags(metadata),
        )

        try:
            record.validate()
        except ValueError as exc:
            warnings.append(str(exc))

        return ImportResult(records=[record], warnings=warnings)


def _split_sections(lines: Iterable[str]) -> tuple[Dict[str, str], List[str], List[str]]:
    metadata: Dict[str, str] = {}
    column_names: List[str] = []
    data_lines: List[str] = []
    in_data = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not in_data and "wavelength" in stripped.lower():
            column_names = [segment.strip() for segment in stripped.replace("\t", " ").split() if segment.strip()]
            in_data = True
            continue
        if in_data:
            data_lines.append(stripped)
        else:
            key, value = _split_metadata_line(stripped)
            if key:
                metadata[key] = value

    return metadata, column_names, data_lines


def _split_metadata_line(line: str) -> tuple[str | None, str]:
    for delimiter in ("=", ":"):
        if delimiter in line:
            key, value = line.split(delimiter, 1)
            return key.strip().title(), value.strip()
    return None, ""


def _parse_numeric_rows(column_names: List[str], data_lines: List[str]) -> Dict[str, Any]:
    wavelengths: List[float] = []
    reflectance: List[float] = []
    radiance: List[float] = []
    warnings: List[str] = []

    col_map = {name.lower(): idx for idx, name in enumerate(column_names)}

    def _find_column(*candidates: str) -> int | None:
        for candidate in candidates:
            for name, idx in col_map.items():
                if candidate in name:
                    return idx
        return None

    wavelength_idx = _find_column("wavelength")
    reflectance_idx = _find_column("reflectance", "ratio")
    radiance_idx = _find_column("radiance", "sample")

    if wavelength_idx is None:
        raise ValueError("ASD data missing wavelength column.")

    for row_number, line in enumerate(data_lines, start=1):
        parts = [segment for segment in line.replace("\t", " ").split() if segment]
        if len(parts) <= wavelength_idx:
            warnings.append(f"Row {row_number}: insufficient columns.")
            continue
        try:
            wavelength_value = float(parts[wavelength_idx])
        except ValueError:
            warnings.append(f"Row {row_number}: invalid wavelength value '{parts[wavelength_idx]}'")
            continue

        wavelengths.append(wavelength_value)

        if reflectance_idx is not None and reflectance_idx < len(parts):
            try:
                reflectance.append(float(parts[reflectance_idx]))
            except ValueError:
                warnings.append(f"Row {row_number}: invalid reflectance value '{parts[reflectance_idx]}'")
        if radiance_idx is not None and radiance_idx < len(parts):
            try:
                radiance.append(float(parts[radiance_idx]))
            except ValueError:
                warnings.append(f"Row {row_number}: invalid radiance value '{parts[radiance_idx]}'")

    reflectance_unit = "ratio" if reflectance else "radiance"

    return {
        "wavelengths": wavelengths,
        "reflectance": reflectance,
        "radiance": radiance,
        "warnings": warnings,
        "reflectance_unit": reflectance_unit,
    }


def _build_tags(metadata: Dict[str, str]) -> List[str]:
    tags = ["asd"]
    instrument = metadata.get("Instrument") or metadata.get("Device")
    if instrument:
        tags.append(instrument.lower().replace(" ", "-"))
    if metadata.get("Units"):
        tags.append(metadata["Units"].lower())
    return tags


register_importer(AsdAsciiImporter())
