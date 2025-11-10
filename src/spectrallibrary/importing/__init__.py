"""Importer interfaces and registry."""

from .base import ImportContext, ImportResult, Importer, SpectrumRecord
from .registry import importer_registry, register_importer

# Ensure built-in importers register themselves
from . import asd_ascii_importer as _asd_importer  # noqa: F401
from . import csv_importer as _csv_importer  # noqa: F401

__all__ = [
    "ImportContext",
    "ImportResult",
    "Importer",
    "SpectrumRecord",
    "importer_registry",
    "register_importer",
]
