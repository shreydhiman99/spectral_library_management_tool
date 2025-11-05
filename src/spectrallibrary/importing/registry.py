"""Registry for importer plugins."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Type

from .base import ImportContext, ImportResult, Importer


class ImporterRegistry:
    """Maintains a mapping of file formats to available importers."""

    def __init__(self) -> None:
        self._importers: List[Importer] = []

    def register(self, importer: Importer) -> None:
        self._importers.append(importer)

    def available_importers(self) -> Sequence[Importer]:
        return tuple(self._importers)

    def find_for_path(self, path: Path) -> List[Importer]:
        return [imp for imp in self._importers if imp.can_handle(path)]

    def import_file(self, path: Path, *, context: ImportContext | None = None) -> ImportResult:
        for importer in self.find_for_path(path):
            result = importer.load(path, context=context)
            if result.records:
                return result
        raise ValueError(f"No importer could handle file: {path}")


def register_importer(importer: Importer) -> Importer:
    importer_registry.register(importer)
    return importer


importer_registry = ImporterRegistry()
