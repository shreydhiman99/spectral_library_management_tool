"""Placeholder export center workspace view."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ExportCenterView(QWidget):
    """Shows a minimal outline of the export configuration surface."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Export Center")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title)

        scope_group = QGroupBox("Scope")
        scope_layout = QFormLayout(scope_group)
        scope_layout.addRow("Source:", QLabel("Current selection"))
        scope_layout.addRow("Include children:", QLabel("Yes"))
        scope_layout.addRow("Latest versions:", QLabel("Yes"))
        layout.addWidget(scope_group)

        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)
        options_layout.addRow("Format:", QLabel("CSV"))
        options_layout.addRow("File naming:", QLabel("{library}_{timestamp}"))
        options_layout.addRow("Include metadata:", QLabel("All"))
        layout.addWidget(options_group)

        queue_group = QGroupBox("Queue")
        queue_layout = QVBoxLayout(queue_group)
        queue_list = QListWidget(queue_group)
        for item in ("Export #17 · Scheduled", "Export #16 · Complete"):
            QListWidgetItem(item, queue_list)
        queue_layout.addWidget(queue_list)
        queue_group.setLayout(queue_layout)
        layout.addWidget(queue_group, 1)

        actions_row = QWidget(self)
        actions_layout = QVBoxLayout(actions_row)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        actions_layout.addWidget(QPushButton("Queue export"))
        actions_layout.addWidget(QPushButton("Open output folder"))
        actions_layout.addStretch(1)
        layout.addWidget(actions_row)

        self.setLayout(layout)
