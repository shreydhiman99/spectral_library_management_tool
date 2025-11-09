from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication

from spectrallibrary.ui import create_application


@pytest.fixture(scope="session")
def ui_app() -> QApplication:
    """Provide a shared QApplication for UI-focused tests."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = create_application([])
    return app
