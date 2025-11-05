"""Registry for exporter implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence

from .base import ExportContext, ExportPayload, Exporter


class ExportRegistry:
    def __init__(self) -> None:
        self._exporters: Dict[str, Exporter] = {}

    def register(self, exporter: Exporter) -> None:
        self._exporters[exporter.format_name] = exporter

    def available_formats(self) -> Sequence[str]:
        return tuple(self._exporters.keys())

    def get(self, format_name: str) -> Exporter:
        try:
            return self._exporters[format_name]
        except KeyError as exc:
            raise ValueError(f"Unknown export format: {format_name}") from exc

    def export(self, format_name: str, payload: ExportPayload, *, context: ExportContext | None = None) -> Path:
        exporter = self.get(format_name)
        return exporter.export(payload, context=context)


def register_exporter(exporter: Exporter) -> Exporter:
    export_registry.register(exporter)
    return exporter


export_registry = ExportRegistry()
