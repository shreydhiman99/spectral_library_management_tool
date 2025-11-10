"""Main window shell for the Spectral Library UI."""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDockWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QWidget,
)

from .widgets.navigation import NavigationDock
from .views import (
    ExportCenterView,
    ImportWizardView,
    LibraryBrowserView,
    PluginHubView,
    SpectrumViewerView,
)
from ..importing import SpectrumRecord
from ..services import ImportSummary


class MainWindow(QMainWindow):
    """Primary application frame, wiring placeholder views."""

    WINDOW_TITLE: Final[str] = "Spectral Library"

    def __init__(self) -> None:
        super().__init__()

        self._stack = QStackedWidget(self)
        self._views = {
            "library": LibraryBrowserView(self),
            "spectra": SpectrumViewerView(self),
            "import": ImportWizardView(self),
            "export": ExportCenterView(self),
            "plugins": PluginHubView(self),
        }

        for view in self._views.values():
            self._stack.addWidget(view)

        self.setCentralWidget(self._stack)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(1280, 800)

        self._navigation_dock: NavigationDock | None = None
        self._pending_viewer_records: list[SpectrumRecord] | None = None
        self._viewer_shortcut_button: QPushButton | None = None
        self._viewer_shortcut_timer: QTimer | None = None

        self._setup_navigation()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_view_signals()

    # region setup helpers
    def _setup_navigation(self) -> None:
        dock = NavigationDock(self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        dock.view_requested.connect(self._handle_view_request)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self._navigation_dock = dock

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Primary", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        toolbar.addAction(self._make_action("Library", "library"))
        toolbar.addAction(self._make_action("Spectra", "spectra"))
        toolbar.addAction(self._make_action("Import", "import"))
        toolbar.addAction(self._make_action("Export", "export"))
        toolbar.addAction(self._make_action("Plugins", "plugins"))

        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar(self)
        status_bar.showMessage("Ready")
        self.setStatusBar(status_bar)

        self._viewer_shortcut_button = QPushButton("View imported spectra", self)
        self._viewer_shortcut_button.setVisible(False)
        self._viewer_shortcut_button.clicked.connect(self._open_last_import_in_viewer)
        status_bar.addPermanentWidget(self._viewer_shortcut_button)

        self._viewer_shortcut_timer = QTimer(self)
        self._viewer_shortcut_timer.setSingleShot(True)
        self._viewer_shortcut_timer.timeout.connect(self._hide_viewer_shortcut)

    # endregion

    def _setup_view_signals(self) -> None:
        import_view = self._views.get("import")
        if hasattr(import_view, "import_completed"):
            import_view.import_completed.connect(self._handle_import_completed)
        if hasattr(import_view, "import_records_ready"):
            import_view.import_records_ready.connect(self._handle_import_records_ready)

    def _make_action(self, text: str, target: str) -> QAction:
        action = QAction(text, self)
        action.triggered.connect(lambda: self._switch_to(target))
        return action

    def _handle_view_request(self, target: str) -> None:
        self._switch_to(target)

    def _switch_to(self, target: str) -> None:
        view = self._views.get(target)
        if view is None:
            return
        self._stack.setCurrentWidget(view)

    def _handle_import_completed(self, summary: ImportSummary) -> None:
        if self._navigation_dock is not None:
            self._navigation_dock.refresh()

        status = self.statusBar()
        if status is not None:
            status.showMessage(
                f"Imported {summary.created_spectra} spectra from import", 5000
            )

    def _handle_import_records_ready(self, records) -> None:
        self._pending_viewer_records = list(records) if records else None
        self._update_viewer_shortcut()

    def _update_viewer_shortcut(self) -> None:
        if self._viewer_shortcut_button is None:
            return

        has_records = bool(self._pending_viewer_records)
        self._viewer_shortcut_button.setVisible(has_records)

        if has_records:
            count = len(self._pending_viewer_records or [])
            label = "View imported spectrum" if count == 1 else "View imported spectra"
            self._viewer_shortcut_button.setText(label)
            if self._viewer_shortcut_timer is not None:
                self._viewer_shortcut_timer.start(10000)
        elif self._viewer_shortcut_timer is not None:
            self._viewer_shortcut_timer.stop()

    def _hide_viewer_shortcut(self) -> None:
        if self._viewer_shortcut_button is not None:
            self._viewer_shortcut_button.setVisible(False)

    def _open_last_import_in_viewer(self) -> None:
        if not self._pending_viewer_records:
            return

        self._switch_to("spectra")
        viewer = self._views.get("spectra")
        if isinstance(viewer, SpectrumViewerView):
            viewer.show_import_preview(self._pending_viewer_records)

        self._pending_viewer_records = None
        if self._viewer_shortcut_timer is not None:
            self._viewer_shortcut_timer.stop()
        self._hide_viewer_shortcut()
