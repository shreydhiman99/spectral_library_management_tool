from __future__ import annotations

import pytest  # type: ignore[import-not-found]

pytest.importorskip("PySide6")

pytestmark = pytest.mark.filterwarnings(
    "ignore:.*AA_EnableHighDpiScaling.*:DeprecationWarning",
    "ignore:.*AA_UseHighDpiPixmaps.*:DeprecationWarning",
)

from spectrallibrary.importing import SpectrumRecord
from spectrallibrary.ui import MainWindow
from spectrallibrary.ui.views.import_wizard import ImportWizardView
from spectrallibrary.ui.views.spectrum_viewer import SpectrumViewerView


def _make_record(material: str) -> SpectrumRecord:
    return SpectrumRecord(
        library_name="QA Library",
        material_name=material,
        category="Reference",
        source="Demo",
        wavelength_unit="nm",
        reflectance_unit="unitless",
        wavelengths=[400.0, 410.0, 420.0],
        reflectance=[0.12, 0.34, 0.56],
        tags=["preview"],
    )


def test_main_window_opens_viewer_for_imported_records(ui_app) -> None:
    window = MainWindow()
    try:
        window.show()
        ui_app.processEvents()

        import_view = window._views.get("import")
        assert isinstance(import_view, ImportWizardView)

        records = [_make_record("Sample A"), _make_record("Sample B")]
        import_view.import_records_ready.emit(records)
        ui_app.processEvents()

        shortcut = window._viewer_shortcut_button
        assert shortcut is not None and shortcut.isVisible()
        assert "spectra" in shortcut.text().lower()

        shortcut.click()
        ui_app.processEvents()

        current = window.centralWidget().currentWidget()
        assert current is window._views["spectra"]
        viewer = window._views["spectra"]
        assert isinstance(viewer, SpectrumViewerView)
        metadata_text = viewer.metadata_label.text()
        assert "Spectra imported: 2" in metadata_text
        assert "Materials represented: 2" in metadata_text
        assert "Libraries represented: 1" in metadata_text

        ui_app.processEvents()
        assert not shortcut.isVisible()
    finally:
        window.close()
        ui_app.processEvents()


def test_main_window_hides_shortcut_when_no_records(ui_app) -> None:
    window = MainWindow()
    try:
        window.show()
        ui_app.processEvents()

        import_view = window._views.get("import")
        assert isinstance(import_view, ImportWizardView)
        viewer = window._views.get("spectra")
        assert isinstance(viewer, SpectrumViewerView)

        import_view.import_records_ready.emit([])
        ui_app.processEvents()

        shortcut = window._viewer_shortcut_button
        assert shortcut is not None
        assert not shortcut.isVisible()

        viewer.show_import_preview([])
        assert viewer.metadata_label.text() == "No spectra selected."
    finally:
        window.close()
        ui_app.processEvents()
