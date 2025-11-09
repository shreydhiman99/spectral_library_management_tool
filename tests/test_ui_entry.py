from __future__ import annotations

import pytest  # type: ignore[import-not-found]

pytest.importorskip("PySide6")

pytestmark = pytest.mark.filterwarnings(
    "ignore:.*AA_EnableHighDpiScaling.*:DeprecationWarning",
    "ignore:.*AA_UseHighDpiPixmaps.*:DeprecationWarning",
)

from PySide6.QtWidgets import QApplication

from spectrallibrary.ui import MainWindow  # noqa: E402


def test_application_sets_expected_metadata(ui_app) -> None:
    assert QApplication.instance() is ui_app
    assert ui_app.applicationName() == "Spectral Library Manager"
    assert ui_app.organizationName() == "SpectralLibrary"


def test_main_window_switches_views(ui_app) -> None:
    window = MainWindow()
    try:
        window._switch_to("library")
        assert window.centralWidget().currentWidget() is window._views["library"]

        window._switch_to("spectra")
        assert window.centralWidget().currentWidget() is window._views["spectra"]
    finally:
        window.close()
        ui_app.processEvents()
