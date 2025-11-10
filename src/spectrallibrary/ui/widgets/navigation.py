"""Navigation dock widgets for the Spectral Library UI shell."""

from __future__ import annotations

from typing import Iterable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QGroupBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...services import LibraryBrowserService
from ...services.library_service import LibraryNode, MaterialNode, SpectrumNode


class LibraryNavigationWidget(QWidget):
    """Provides hierarchical navigation and quick facet filters."""

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        service: Optional[LibraryBrowserService] = None,
    ) -> None:
        super().__init__(parent)

        self._service = service or LibraryBrowserService()

        self.filter_hint = QLabel("Filter libraries and materials")
        self.filter_hint.setObjectName("LibraryFilterHint")

        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        self.facets_box = QGroupBox("Facets", self)
        self.facets_box.setFlat(True)

        facets_layout = QVBoxLayout(self.facets_box)
        facets_layout.setContentsMargins(8, 4, 8, 8)
        facets_layout.setSpacing(4)

        for label in ("Igneous", "Sedimentary", "Metamorphic", "Uncategorized"):
            checkbox = QCheckBox(label, self.facets_box)
            checkbox.setTristate(False)
            facets_layout.addWidget(checkbox)

        self.background_box = QGroupBox("Background tasks", self)
        self.background_box.setFlat(True)
        bg_layout = QVBoxLayout(self.background_box)
        bg_layout.setContentsMargins(8, 4, 8, 8)
        self.task_list = QListWidget(self.background_box)
        self.task_list.addItems(["Import queue is empty."])
        self.task_list.setAlternatingRowColors(True)
        self.task_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        bg_layout.addWidget(self.task_list)
        self.background_box.setLayout(bg_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(self.filter_hint)
        layout.addWidget(self.tree, 1)
        layout.addWidget(self.facets_box)
        layout.addWidget(self.background_box)

        self.refresh()

    def refresh(self) -> None:
        """Reload navigation content from the service."""

        libraries = self._service.fetch_library_tree()
        self.tree.clear()

        if not libraries:
            placeholder = QTreeWidgetItem(["No materials found yet"])
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self.tree.addTopLevelItem(placeholder)
            return

        for library in libraries:
            library_item = self._make_library_item(library)
            self.tree.addTopLevelItem(library_item)

        self.tree.expandToDepth(1)

    def selected_hierarchy(self) -> Iterable[str]:
        """Return the text of the selected tree item and its parents."""

        item = self.tree.currentItem()
        while item is not None:
            yield item.text(0)
            item = item.parent()

    # ------------------------------------------------------------------
    # Tree construction helpers

    def _make_library_item(self, library: LibraryNode) -> QTreeWidgetItem:
        item = QTreeWidgetItem([library.name])
        item.setData(0, Qt.ItemDataRole.UserRole, {"type": "library", "name": library.name})

        for material in library.materials:
            item.addChild(self._make_material_item(material))

        return item

    def _make_material_item(self, material: MaterialNode) -> QTreeWidgetItem:
        label = f"{material.name} · {material.category}"
        item = QTreeWidgetItem([label])
        item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            {"type": "material", "id": material.id, "name": material.name},
        )

        for spectrum in material.spectra:
            item.addChild(self._make_spectrum_item(spectrum))

        return item

    def _make_spectrum_item(self, spectrum: SpectrumNode) -> QTreeWidgetItem:
        item = QTreeWidgetItem([spectrum.label])
        item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            {
                "type": "spectrum",
                "id": spectrum.id,
                "source": spectrum.source,
                "quality": spectrum.quality_status,
            },
        )
        return item


class ContextSummaryWidget(QWidget):
    """Right-hand context panel showing metadata, tasks, and plugin slots."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        self.metadata_group = _info_group(
            "Metadata",
            [
                "Material: Basalt-01",
                "Library: Global Reference",
                "Source: ASD FieldSpec 4",
                "Status: In review",
            ],
        )
        layout.addWidget(self.metadata_group)

        self.activity_group = _info_group(
            "Activity",
            [
                "• Imported 3 minutes ago",
                "• Tagged by analyst",
                "• No outstanding checks",
            ],
        )
        layout.addWidget(self.activity_group)

        self.plugin_group = _info_group(
            "Plugin widgets",
            [
                "Plugins can inject additional controls here.",
                "Use the Plugin Hub to enable extensions.",
            ],
        )
        layout.addWidget(self.plugin_group)

        layout.addStretch(1)


def _info_group(title: str, lines: Iterable[str]) -> QGroupBox:
    group = QGroupBox(title)
    group.setFlat(True)
    layout = QVBoxLayout(group)
    layout.setContentsMargins(8, 4, 8, 8)
    layout.setSpacing(4)
    for line in lines:
        lbl = QLabel(line)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
    return group


class NavigationDock(QDockWidget):
    """Combined navigation and context dock for the main window."""

    view_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Navigation", parent)
        self.setObjectName("NavigationDock")

        content = QWidget(self)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.navigation = LibraryNavigationWidget(content)
        self.summary = ContextSummaryWidget(content)

        layout.addWidget(self.navigation)
        layout.addWidget(self.summary)

        content.setLayout(layout)
        self.setWidget(content)

        self.navigation.tree.itemActivated.connect(self._handle_tree_activation)

    def _handle_tree_activation(self, item: QTreeWidgetItem) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(data, dict):
            target_type = data.get("type")
            mapping = {
                "library": "library",
                "material": "spectra",
                "spectrum": "spectra",
            }
            if target_type in mapping:
                self.view_requested.emit(mapping[target_type])

    def refresh(self) -> None:
        """Reload navigation data from the underlying service."""

        self.navigation.refresh()
