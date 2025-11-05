"""Core protocols and payloads for spectral exporters."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Protocol, Sequence

from spectrallibrary.importing import SpectrumRecord


@dataclass(slots=True)
class ExportPayload:
    """Data to be exported, expressed as normalized spectrum records."""

    spectra: Sequence[SpectrumRecord]
    output_path: Path


@dataclass(slots=True)
class ExportContext:
    """Context modifiers for exporters (format options, user preferences)."""

    options: Mapping[str, str] | None = None


class Exporter(Protocol):
    """Protocol that all exporters must conform to."""

    format_name: str

    def export(self, payload: ExportPayload, *, context: ExportContext | None = None) -> Path:
        ...
