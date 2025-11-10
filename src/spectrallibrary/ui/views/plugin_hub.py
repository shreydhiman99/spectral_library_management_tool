"""Placeholder plugin hub workspace view."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class PluginHubView(QWidget):
    """Displays placeholder information about available plugins."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Plugin Hub")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title)

        highlight_area = QScrollArea(self)
        highlight_area.setWidgetResizable(True)

        highlight_widget = QWidget(highlight_area)
        grid = QGridLayout(highlight_widget)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        featured_plugins = [
            ("SpecSync", "Synchronize collections across workspaces"),
            ("ColorMap Plus", "Enhanced rendering for complex spectra"),
            ("Exporter Pro", "Publish datasets with quality presets"),
        ]

        for index, (name, desc) in enumerate(featured_plugins):
            name_label = QLabel(name)
            desc_label = QLabel(desc)
            desc_label.setWordWrap(True)

            install_btn = QPushButton("Install")
            install_btn.setIcon(QIcon.fromTheme("download"))

            grid.addWidget(name_label, index, 0)
            grid.addWidget(desc_label, index, 1)
            grid.addWidget(install_btn, index, 2)

        highlight_widget.setLayout(grid)
        highlight_area.setWidget(highlight_widget)
        layout.addWidget(highlight_area, 1)

        catalog_group = QListWidget(self)
        for name in ("Importer Bridge", "Normalization Toolkit", "Peak Finder AI"):
            item = QListWidgetItem(name)
            item.setIcon(QIcon.fromTheme("plugin"))
            catalog_group.addItem(item)
        layout.addWidget(catalog_group, 1)

        manage_row = QWidget(self)
        manage_layout = QVBoxLayout(manage_row)
        manage_layout.setContentsMargins(0, 0, 0, 0)
        manage_layout.setSpacing(6)
        manage_layout.addWidget(QPushButton("Manage installed plugins"))
        manage_layout.addWidget(QPushButton("Open plugin directory"))
        manage_row.setLayout(manage_layout)
        layout.addWidget(manage_row)

        self.setLayout(layout)
