"""Application helpers for the PySide6 UI shell."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

_HIGH_DPI_ATTRIBUTES: tuple[Qt.ApplicationAttribute, ...] = (
    Qt.ApplicationAttribute.AA_EnableHighDpiScaling,
    Qt.ApplicationAttribute.AA_UseHighDpiPixmaps,
)


def _set_high_dpi_attributes() -> None:
    for attribute in _HIGH_DPI_ATTRIBUTES:
        QApplication.setAttribute(attribute, True)


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Return a configured :class:`~PySide6.QtWidgets.QApplication` instance."""

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    _set_high_dpi_attributes()
    _ensure_font_configuration()

    args = list(argv) if argv is not None else sys.argv
    app = QApplication(args)
    app.setApplicationName("Spectral Library Manager")
    app.setOrganizationName("SpectralLibrary")
    app.setOrganizationDomain("spectrallibrary.local")
    app.setQuitOnLastWindowClosed(True)

    style_override = os.environ.get("SPECTRALLIBRARY_QT_STYLE")
    if style_override:
        app.setStyle(style_override)

    return app


# ---------------------------------------------------------------------------
# Font helpers


def _ensure_font_configuration() -> None:
    """Set ``QT_QPA_FONTDIR`` when no fonts are bundled with Qt/PySide."""

    current = os.environ.get("QT_QPA_FONTDIR")
    if current and Path(current).exists():
        return

    for candidate in _candidate_font_dirs():
        if candidate.exists():
            os.environ["QT_QPA_FONTDIR"] = str(candidate)
            break


def _candidate_font_dirs() -> Iterable[Path]:
    """Yield platform-aware font directories to test in order."""

    override = os.environ.get("SPECTRALLIBRARY_FONT_DIR")
    if override:
        yield Path(override)

    if sys.platform.startswith("win"):
        windir = os.environ.get("WINDIR", r"C:\\Windows")
        yield Path(windir) / "Fonts"
    elif sys.platform == "darwin":
        yield Path("/System/Library/Fonts")
        yield Path("/Library/Fonts")
    else:
        linux_candidates = (
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".local/share/fonts",
        )
        for path in linux_candidates:
            yield path
