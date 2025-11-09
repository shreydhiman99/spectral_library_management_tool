from __future__ import annotations

import csv

import pytest  # type: ignore[import-not-found]

pytest.importorskip("PySide6")

pytestmark = pytest.mark.filterwarnings(
    "ignore:.*AA_EnableHighDpiScaling.*:DeprecationWarning",
    "ignore:.*AA_UseHighDpiPixmaps.*:DeprecationWarning",
)

from PySide6.QtWidgets import QDialogButtonBox, QFileDialog

from spectrallibrary.importing import ImportResult, SpectrumRecord
from spectrallibrary.ui.views.import_wizard import ImportPreviewDialog


def _make_record(material: str, reflectance: list[float] | None = None) -> SpectrumRecord:
    values = reflectance or [0.12, 0.34, 0.56]
    wavelengths = [400.0 + 10.0 * index for index in range(len(values))]
    return SpectrumRecord(
        library_name="QA Library",
        material_name=material,
        category="Reference",
        source="Demo",
        wavelength_unit="nm",
        reflectance_unit="unitless",
        wavelengths=wavelengths,
        reflectance=values,
        tags=["preview"],
    )


def _find_button(dialog: ImportPreviewDialog, text: str):
    button_box = dialog.findChild(QDialogButtonBox)
    assert button_box is not None, "dialog should include a button box"
    for button in button_box.buttons():
        if button.text() == text:
            return button
    pytest.fail(f"button with text {text!r} not found")


def test_preview_export_selected_record(ui_app, tmp_path, monkeypatch) -> None:
    export_path = tmp_path / "selected.csv"
    source_path = tmp_path / "source.csv"
    source_path.write_text("dummy source", encoding="utf-8")

    record = _make_record("Sample A")
    result = ImportResult(records=[record])

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_, **__: (str(export_path), "csv"),
    )

    dialog = ImportPreviewDialog(source_path, result)
    dialog.show()

    button = _find_button(dialog, "Export selected…")
    button.click()
    ui_app.processEvents()

    with export_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    assert len(rows) == 4
    assert rows[0] == ["Wavelength (nm)", "Reflectance (unitless)"]

    wavelengths = [float(row[0]) for row in rows[1:]]
    reflectance = [float(row[1]) for row in rows[1:]]
    assert wavelengths == pytest.approx([400.0, 410.0, 420.0])
    assert reflectance == pytest.approx([0.12, 0.34, 0.56])

    dialog.close()
    ui_app.processEvents()


def test_preview_export_all_records(ui_app, tmp_path, monkeypatch) -> None:
    export_path = tmp_path / "preview.csv"
    source_path = tmp_path / "import.csv"
    source_path.write_text("dummy source", encoding="utf-8")

    records = [
        _make_record("Sample A"),
        _make_record("Sample B", reflectance=[0.21, 0.22, 0.23]),
    ]
    result = ImportResult(records=records)

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_, **__: (str(export_path), "csv"),
    )

    dialog = ImportPreviewDialog(source_path, result)
    dialog.show()

    button = _find_button(dialog, "Export all previewed…")
    button.click()
    ui_app.processEvents()

    with export_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    header = rows[0]
    assert header[:4] == ["library_name", "material_name", "category", "source"]
    assert rows[1][1] == "Sample A"
    assert rows[2][1] == "Sample B"
    assert rows[2][6] == "400;410;420"

    dialog.close()
    ui_app.processEvents()
