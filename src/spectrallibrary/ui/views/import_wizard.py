"""Import wizard workspace view backed by importer services."""

from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal, Slot, QThread
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHeaderView,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...importing import ImportContext, ImportResult, SpectrumRecord, importer_registry
from ...services import ImportService, ImportSummary


class ImportWizardView(QWidget):
    """Simple stacked widget mimicking a multi-step import flow."""

    import_completed = Signal(object)
    import_records_ready = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Import Wizard")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title)

        self.stepper = StepperWidget(self)
        layout.addWidget(self.stepper, 1)

        self._service = ImportService()
        self._worker_thread: QThread | None = None
        self._worker: ImportWorker | None = None
        self._last_directory = str(Path.home())
        self._last_import_result: ImportResult | None = None
        self._last_import_path: Path | None = None

        options_group = QGroupBox("Options", self)
        options_layout = QFormLayout(options_group)
        self.library_override = QLineEdit(options_group)
        self.library_override.setPlaceholderText("Override library name (optional)")
        options_layout.addRow("Target library", self.library_override)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        status_group = QGroupBox("Last import", self)
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(8)
        self.status_label = QLabel("No imports executed yet.", status_group)
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        self.import_progress = QProgressBar(status_group)
        self.import_progress.setVisible(False)
        self.import_progress.setRange(0, 1)
        self.import_progress.setValue(0)
        self.import_progress.setFormat("")
        status_layout.addWidget(self.import_progress)

        self.warning_list = QListWidget(status_group)
        self.warning_list.setVisible(False)
        status_layout.addWidget(self.warning_list)

        self.view_details_button = QPushButton("View imported records…", status_group)
        self.view_details_button.setVisible(False)
        self.view_details_button.clicked.connect(self._handle_view_import_details)
        status_layout.addWidget(self.view_details_button)

        layout.addWidget(status_group)

        button_row = QWidget(self)
        button_layout = QVBoxLayout(button_row)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(6)

        self.import_button = QPushButton("Import spectral file…")
        self.import_button.clicked.connect(self._handle_launch_import)
        button_layout.addWidget(self.import_button)

        self.preview_button = QPushButton("Preview mapping")
        self.preview_button.clicked.connect(self._handle_preview)
        button_layout.addWidget(self.preview_button)
        button_layout.addStretch(1)

        layout.addWidget(button_row)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Slots

    def _handle_launch_import(self) -> None:
        selected_path = self._choose_file("Select spectral file")
        if selected_path is None:
            return

        context = ImportContext(target_library=self.library_override.text().strip() or None)
        self._start_import(selected_path, context)

    def _handle_preview(self) -> None:
        selected_path = self._choose_file("Preview spectral file")
        if selected_path is None:
            return

        context = ImportContext(target_library=self.library_override.text().strip() or None)

        try:
            result = importer_registry.import_file(selected_path, context=context)
        except Exception as exc:  # pragma: no cover - UI safeguard
            QMessageBox.warning(self, "Preview failed", f"Unable to preview file:\n{exc}")
            return

        dialog = ImportPreviewDialog(selected_path, result, parent=self)
        dialog.exec()

    def _start_import(self, file_path: Path, context: ImportContext | None) -> None:
        self._set_import_running(True)

        worker = ImportWorker(self._service, file_path, context)
        thread = QThread(self)

        worker.moveToThread(thread)
        thread.started.connect(worker.run)

        worker.progress.connect(self._handle_import_progress)
        worker.completed.connect(self._handle_import_completed)
        worker.failed.connect(self._handle_import_failed)

        worker.completed.connect(lambda *_: self._cleanup_worker())
        worker.failed.connect(lambda *_: self._cleanup_worker())
        thread.finished.connect(thread.deleteLater)

        self._worker = worker
        self._worker_thread = thread

        thread.start()

    def _handle_import_progress(self, processed: int, total: int) -> None:
        if total <= 0:
            self.import_progress.setRange(0, 0)
            self.import_progress.setFormat("Processing…")
        else:
            if self.import_progress.maximum() != total:
                self.import_progress.setRange(0, total)
            self.import_progress.setValue(processed)
            self.import_progress.setFormat(f"{processed} / {total} records")

        if not self.import_progress.isVisible():
            self.import_progress.setVisible(True)

    def _handle_import_completed(
        self, summary: ImportSummary, file_name: str, result: ImportResult
    ) -> None:
        self._set_import_running(False)
        self._update_status(summary, file_name)
        self._last_import_result = result
        self._last_import_path = Path(file_name)

        self.import_records_ready.emit(result.records)

        has_details = bool(result.records) or bool(result.warnings)
        self.view_details_button.setVisible(has_details)
        self.view_details_button.setEnabled(has_details)

        self.import_completed.emit(summary)

        if summary.created_spectra == 0:
            if summary.warnings:
                QMessageBox.warning(  # pragma: no cover - UI feedback
                    self,
                    "Import completed with warnings",
                    (
                        "No spectra were imported from the selected file. "
                        "See warnings below for details."
                    ),
                )
            else:
                QMessageBox.information(  # pragma: no cover - UI feedback
                    self,
                    "Import completed",
                    "No spectra were imported from the selected file.",
                )

    def _handle_import_failed(self, message: str) -> None:  # pragma: no cover - UI safeguard
        self._set_import_running(False)
        QMessageBox.critical(self, "Import failed", f"Unable to import file:\n{message}")

    def _set_import_running(self, running: bool) -> None:
        self.import_button.setDisabled(running)
        self.preview_button.setDisabled(running)
        if running:
            self.status_label.setText("Import in progress…")
            self.import_progress.setVisible(True)
            self.import_progress.setRange(0, 0)
            self.import_progress.setFormat("Processing…")
            self.view_details_button.setVisible(False)
        else:
            self.import_progress.setRange(0, 1)
            self.import_progress.setValue(0)
            self.import_progress.setFormat("")

    def _cleanup_worker(self) -> None:
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait()
            self._worker_thread = None
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

    def closeEvent(self, event):  # pragma: no cover - UI lifecycle hook
        self._cleanup_worker()
        super().closeEvent(event)

    def _choose_file(self, title: str) -> Path | None:
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            title,
            self._last_directory,
            "Spectral files (*.csv *.sig *.txt)",
        )
        if not file_name:
            return None

        path = Path(file_name)
        self._last_directory = str(path.parent)
        return path

    def _update_status(self, summary: ImportSummary, file_name: str) -> None:
        if summary.created_spectra:
            status_text = (
                f"Imported {summary.created_spectra} spectra across {summary.created_materials} materials "
                f"from {Path(file_name).name}."
            )
        else:
            status_text = f"No spectra were imported from {Path(file_name).name}."

        self.status_label.setText(status_text)

        self.warning_list.clear()
        if summary.warnings:
            for warning in summary.warnings:
                QListWidgetItem(warning, self.warning_list)
            self.warning_list.setVisible(True)
        else:
            self.warning_list.setVisible(False)

        self.import_progress.setVisible(False)
        self.import_progress.setRange(0, 1)
        self.import_progress.setValue(0)
        self.import_progress.setFormat("")

    def _handle_view_import_details(self) -> None:
        if self._last_import_result is None or self._last_import_path is None:
            return
        dialog = ImportPreviewDialog(self._last_import_path, self._last_import_result, parent=self)
        dialog.exec()


class StepperWidget(QStackedWidget):
    steps = (
        "Select Files",
        "Map Columns",
        "Metadata Rules",
        "Review",
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        for index, name in enumerate(self.steps, start=1):
            self.addWidget(self._build_step(index, name))

    def _build_step(self, index: int, name: str) -> QWidget:
        widget = QGroupBox(f"Step {index}: {name}")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        description = QLabel(
            "This is a placeholder for the detailed wizard layout. "
            "Each step will surface specific controls, previews, and validation messages."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        progress = QProgressBar(widget)
        progress.setRange(0, len(self.steps))
        progress.setValue(index)
        layout.addWidget(progress)

        layout.addStretch(1)
        return widget


class ImportWorker(QObject):
    progress = Signal(int, int)
    completed = Signal(object, str, object)
    failed = Signal(str)

    def __init__(self, service: ImportService, path: Path, context: ImportContext | None) -> None:
        super().__init__()
        self._service = service
        self._path = path
        self._context = context

    @Slot()
    def run(self) -> None:
        try:
            summary, result = self._service.import_with_result(
                self._path,
                context=self._context,
                progress_callback=self._report_progress,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.failed.emit(str(exc))
            return
        self.completed.emit(summary, str(self._path), result)

    def _report_progress(self, processed: int, total: int) -> None:
        self.progress.emit(processed, total)


class ImportPreviewDialog(QDialog):
    """Simple preview dialog showing parsed records from an import file."""

    def __init__(self, path: Path, result: ImportResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Preview: {path.name}")
        self.resize(760, 520)

        self._source_path = path
        self._all_records = result.records

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        summary = QLabel(
            (
                f"Found {len(result.records)} record(s) in {path.name}. "
                "Only the first 10 records are shown below."
            ),
            self,
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)

        self._records = self._all_records[:10]
        self._detail_text: QTextEdit | None = None
        self._selected_row = 0 if self._records else -1
        self._copy_button: QPushButton | None = None
        self._export_button: QPushButton | None = None
        self._export_all_button: QPushButton | None = None

        if self._records:
            table = QTableWidget(len(self._records), 7, self)
            table.setHorizontalHeaderLabels(
                [
                    "Library",
                    "Material",
                    "Category",
                    "Source",
                    "Wavelength range",
                    "Reflectance sample",
                    "Tags",
                ]
            )
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

            for row_index, record in enumerate(self._records):
                table.setItem(row_index, 0, QTableWidgetItem(record.library_name))
                table.setItem(row_index, 1, QTableWidgetItem(record.material_name))
                table.setItem(row_index, 2, QTableWidgetItem(record.category or ""))
                table.setItem(row_index, 3, QTableWidgetItem(record.source or ""))

                wavelength_text = _format_wavelength_range(record)
                table.setItem(row_index, 4, QTableWidgetItem(wavelength_text))

                reflectance_text = _format_reflectance_preview(record)
                table.setItem(row_index, 5, QTableWidgetItem(reflectance_text))

                table.setItem(row_index, 6, QTableWidgetItem("; ".join(record.tags)))

            table.cellClicked.connect(self._handle_row_selected)
            layout.addWidget(table)

            detail_label = QLabel("Selected record details", self)
            layout.addWidget(detail_label)

            detail_text = QTextEdit(self)
            detail_text.setReadOnly(True)
            detail_text.setMinimumHeight(140)
            layout.addWidget(detail_text)

            self._detail_text = detail_text
            self._update_detail_text(0)
        else:
            empty_label = QLabel("No records were parsed from this file.", self)
            layout.addWidget(empty_label)

        if result.warnings:
            warnings_group = QGroupBox("Warnings", self)
            warnings_layout = QVBoxLayout(warnings_group)
            warnings_layout.setContentsMargins(8, 8, 8, 8)
            warnings_layout.setSpacing(4)

            warnings_list = QListWidget(warnings_group)
            for warning in result.warnings:
                QListWidgetItem(warning, warnings_list)
            warnings_layout.addWidget(warnings_list)
            layout.addWidget(warnings_group)

        buttons = QDialogButtonBox(self)
        copy_button = buttons.addButton("Copy details", QDialogButtonBox.ButtonRole.ActionRole)
        export_button = buttons.addButton("Export selected…", QDialogButtonBox.ButtonRole.ActionRole)
        export_all_button = buttons.addButton(
            "Export all previewed…", QDialogButtonBox.ButtonRole.ActionRole
        )
        close_button = buttons.addButton(QDialogButtonBox.StandardButton.Close)

        copy_button.clicked.connect(self._handle_copy_details)
        export_button.clicked.connect(self._handle_export_csv)
        export_all_button.clicked.connect(self._handle_export_all_csv)
        close_button.clicked.connect(self.reject)
        buttons.rejected.connect(self.reject)

        has_records = bool(self._records)
        copy_button.setEnabled(has_records and self._detail_text is not None)
        export_button.setEnabled(has_records)
        export_all_button.setEnabled(has_records)

        self._copy_button = copy_button
        self._export_button = export_button
        self._export_all_button = export_all_button

        layout.addWidget(buttons)

    def _handle_row_selected(self, row: int, _column: int) -> None:
        self._update_detail_text(row)

    def _update_detail_text(self, row: int) -> None:
        if self._detail_text is None or not self._records:
            return
        row = max(0, min(row, len(self._records) - 1))
        record = self._records[row]
        self._selected_row = row

        wavelengths_preview = ", ".join(f"{value:.2f}" for value in record.wavelengths[:12])
        if len(record.wavelengths) > 12:
            wavelengths_preview += " …"

        reflectance_preview = ", ".join(f"{value:.4f}" for value in record.reflectance[:12])
        if len(record.reflectance) > 12:
            reflectance_preview += " …"

        lines = [
            f"Library: {record.library_name}",
            f"Material: {record.material_name}",
            f"Category: {record.category or '-'}",
            f"Source: {record.source or '-'}",
            f"Tags: {'; '.join(record.tags) if record.tags else '-'}",
            "",
            f"Wavelength range: {_format_wavelength_range(record)}",
            "Wavelength samples:",
            wavelengths_preview or "(none)",
            "",
            f"Reflectance unit: {record.reflectance_unit}",
            "Reflectance samples:",
            reflectance_preview or "(none)",
        ]

        self._detail_text.setPlainText("\n".join(lines))

    def _current_record(self) -> SpectrumRecord | None:
        if not self._records:
            return None
        if self._selected_row < 0 or self._selected_row >= len(self._records):
            return None
        return self._records[self._selected_row]

    def _handle_copy_details(self) -> None:
        if self._detail_text is None:
            return
        text = self._detail_text.toPlainText().strip()
        if not text:
            return
        QApplication.clipboard().setText(text)

    def _handle_export_csv(self) -> None:
        record = self._current_record()
        if record is None:
            return

        default_name = f"{record.material_name or 'spectrum'}.csv"
        default_path = (
            self._source_path.parent / default_name
            if self._source_path is not None and self._source_path.exists()
            else Path(default_name)
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export spectrum data",
            str(default_path),
            "CSV files (*.csv);;All files (*.*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        f"Wavelength ({record.wavelength_unit})",
                        f"Reflectance ({record.reflectance_unit})",
                    ]
                )
                for wavelength, reflectance in zip(record.wavelengths, record.reflectance):
                    writer.writerow([wavelength, reflectance])
        except Exception as exc:  # pragma: no cover - UI safeguard
            QMessageBox.critical(
                self,
                "Export failed",
                f"Unable to export spectrum data:\n{exc}",
            )

    def _handle_export_all_csv(self) -> None:
        if not self._all_records:
            return

        default_name = (
            f"{self._source_path.stem}_preview.csv"
            if self._source_path is not None
            else "spectra_preview.csv"
        )
        default_path = (
            self._source_path.parent / default_name
            if self._source_path is not None and self._source_path.exists()
            else Path(default_name)
        )

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export previewed spectra",
            str(default_path),
            "CSV files (*.csv);;All files (*.*)",
        )
        if not file_path:
            return

        header = [
            "library_name",
            "material_name",
            "category",
            "source",
            "wavelength_unit",
            "reflectance_unit",
            "wavelengths",
            "reflectance",
            "tags",
            "acquisition_date",
            "location",
            "comments",
        ]

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                for record in self._all_records:
                    writer.writerow(_record_to_csv_row(record))
        except Exception as exc:  # pragma: no cover - UI safeguard
            QMessageBox.critical(
                self,
                "Export failed",
                f"Unable to export previewed spectra:\n{exc}",
            )


def _format_wavelength_range(record: SpectrumRecord) -> str:
    wavelengths = record.wavelengths
    if not wavelengths:
        return "—"

    start = float(wavelengths[0])
    end = float(wavelengths[-1])
    total = len(wavelengths)
    unit = record.wavelength_unit

    if total == 1:
        return f"{start:.2f} {unit}"

    return f"{start:.2f} – {end:.2f} {unit} ({total} samples)"


def _format_reflectance_preview(record: SpectrumRecord) -> str:
    reflectance = record.reflectance
    if not reflectance:
        return "—"

    minimum = min(reflectance)
    maximum = max(reflectance)
    unit = record.reflectance_unit

    if abs(maximum - minimum) < 1e-9:
        return f"{minimum:.4f} {unit}"

    return f"{minimum:.4f} – {maximum:.4f} {unit}"


def _record_to_csv_row(record: SpectrumRecord) -> list[str]:
    return [
        record.library_name,
        record.material_name,
        record.category or "",
        record.source or "",
        record.wavelength_unit,
        record.reflectance_unit,
        ";".join(f"{value:g}" for value in record.wavelengths),
        ";".join(f"{value:g}" for value in record.reflectance),
        ";".join(record.tags),
        record.acquisition_date.isoformat() if record.acquisition_date else "",
        record.location or "",
        record.comments or "",
    ]
