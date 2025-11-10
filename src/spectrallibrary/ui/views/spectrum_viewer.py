"""Placeholder spectrum viewer workspace view."""

from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ...importing import SpectrumRecord


class SpectrumViewerView(QWidget):
    """Shows temporary widgets that mimic the intended spectrum viewer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(12)

        header = QLabel("Spectrum Viewer")
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        outer_layout.addWidget(header)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        self.compare_button = QPushButton("Compare…")
        self.normalize_button = QPushButton("Normalize")
        self.markers_button = QPushButton("Markers")
        self.export_button = QPushButton("Export Plot")

        for button in (
            self.compare_button,
            self.normalize_button,
            self.markers_button,
            self.export_button,
        ):
            toolbar_layout.addWidget(button)

        toolbar_layout.addStretch(1)
        outer_layout.addLayout(toolbar_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(4)

        plot_placeholder = _plot_group()
        splitter.addWidget(plot_placeholder)

        metadata_panel, self.metadata_label, self.version_list = _metadata_group()
        splitter.addWidget(metadata_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        outer_layout.addWidget(splitter, 1)

        self._current_records: list[SpectrumRecord] = []

        self.setLayout(outer_layout)

    def show_import_preview(self, records: Sequence[SpectrumRecord]) -> None:
        if not records:
            self._current_records = []
            self.metadata_label.setText("No spectra selected.")
            self.version_list.clear()
            return

        self._current_records = list(records)
        first = self._current_records[0]
        total = len(self._current_records)
        unique_materials = len({record.material_name for record in self._current_records})
        unique_libraries = len({record.library_name for record in self._current_records})

        self.metadata_label.setText(
            (
                f"Spectra imported: {total}\n"
                f"Materials represented: {unique_materials}\n"
                f"Libraries represented: {unique_libraries}\n"
                "\n"
                f"First record — Material: {first.material_name}\n"
                f"Library: {first.library_name}\n"
                f"Source: {first.source}\n"
                f"Wavelength unit: {first.wavelength_unit}\n"
                f"Reflectance unit: {first.reflectance_unit}"
            )
        )

        self.version_list.clear()
        for record in self._current_records:
            description = (
                f"{record.material_name} · {len(record.wavelengths)} samples · "
                f"Library: {record.library_name} · "
                f"Tags: {', '.join(record.tags) if record.tags else 'none'}"
            )
            QListWidgetItem(description, self.version_list)
        if self.version_list.count():
            self.version_list.setCurrentRow(0)


def _plot_group() -> QGroupBox:
    group = QGroupBox("Interactive Plot Placeholder")
    group_layout = QVBoxLayout(group)
    group_layout.setContentsMargins(16, 16, 16, 16)
    label = QLabel(
        "A PyQtGraph widget will render spectra overlays here. "
        "Zoom, pan, and marker controls will be wired in upcoming iterations."
    )
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setMinimumHeight(260)
    group_layout.addWidget(label)
    return group


def _metadata_group() -> tuple[QGroupBox, QLabel, QListWidget]:
    group = QGroupBox("Metadata & Version History")
    layout = QVBoxLayout(group)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    metadata = QLabel(
        "Material: Basalt-01\n"
        "Library: Global Reference\n"
        "Source: ASD FieldSpec 4\n"
        "Status: In review"
    )
    metadata.setWordWrap(True)
    layout.addWidget(metadata)

    version_list = QListWidget(group)
    for text in (
        "v3 · Imported from CSV · 2024-03-18",
        "v2 · Metadata edit · 2024-03-10",
        "v1 · Initial ingestion · 2024-02-28",
    ):
        QListWidgetItem(text, version_list)
    version_list.setAlternatingRowColors(True)
    layout.addWidget(version_list)

    return group, metadata, version_list
