"""Placeholder implementation of the library browser workspace view."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class LibraryBrowserView(QWidget):
    """Displays a materials grid with placeholder data."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Library Browser")
        title.setObjectName("LibraryBrowserTitle")
        title.setProperty("class", "h1")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Explore libraries, materials, and spectra. Real data wiring coming soon."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        table = QTableWidget(5, 5, self)
        table.setHorizontalHeaderLabels(
            [
                "Material",
                "Library",
                "Spectra",
                "Category",
                "Status",
            ]
        )
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        demo_rows = [
            ("Basalt-01", "Global Reference", "12", "Igneous", "Review"),
            ("Basalt-02", "Global Reference", "9", "Igneous", "Complete"),
            ("Sandstone-01", "Sediment Study", "8", "Sedimentary", "Complete"),
            ("Ice-12", "Ice Samples", "4", "Glacial", "Incomplete"),
            ("Soil-04", "Soil Cores", "7", "Soil", "Review"),
        ]
        for row, values in enumerate(demo_rows):
            for column, value in enumerate(values):
                table.setItem(row, column, QTableWidgetItem(value))

        layout.addWidget(table, 1)

        footer = QLabel(
            "Bulk actions, filtering, and saved views will appear along the bottom toolbar."
        )
        footer.setWordWrap(True)
        footer.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(footer)

        self.setLayout(layout)
