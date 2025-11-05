"""Core protocols and data structures for spectral importers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Protocol, Sequence


@dataclass(slots=True)
class SpectrumRecord:
    """Normalized representation of an imported spectrum."""

    library_name: str
    material_name: str
    category: str
    source: str
    wavelength_unit: str
    reflectance_unit: str
    wavelengths: Sequence[float]
    reflectance: Sequence[float]
    location: Optional[str] = None
    acquisition_date: Optional[date] = None
    comments: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def validate(self) -> None:
        if len(self.wavelengths) != len(self.reflectance):
            raise ValueError("wavelengths and reflectance must have equal length")
        if not self.wavelengths:
            raise ValueError("spectrum must contain at least one data point")


@dataclass(slots=True)
class ImportContext:
    """Context provided to importers (user options, target paths, etc.)."""

    target_library: Optional[str] = None
    extra_options: Mapping[str, str] | None = None


@dataclass(slots=True)
class ImportResult:
    """Result from an importer execution."""

    records: List[SpectrumRecord] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class Importer(Protocol):
    """Protocol that all importers must implement."""

    formats: Sequence[str]

    def can_handle(self, path: Path) -> bool:
        ...

    def load(self, path: Path, *, context: ImportContext | None = None) -> ImportResult:
        ...
