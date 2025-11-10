# Architecture Overview

## Layered view
- **Presentation layer**: PySide6-based desktop UI (main window, dockable panels, import wizard, spectrum viewer).
- **Application services**: Coordinators for import/export, search, visualization, plugin management, task scheduling.
- **Domain layer**: Entities (Material, Spectrum, SpectrumVersion, PluginManifest) and validation rules using Pydantic models.
- **Persistence**: SQLite database accessed via SQLAlchemy ORM and repositories, with Alembic migrations.
- **Extension platform**: Plugin SDK exposing high-level service interfaces and lifecycle hooks.

## Key modules
- `spectrallibrary.app`: application bootstrap, dependency injection, event loop management.
- `spectrallibrary.db`: engine factory, session management, migrations helpers.
- `spectrallibrary.importers`: built-in import providers, registry, schema mappers.
- `spectrallibrary.exporters`: serializers and formatter templates.
- `spectrallibrary.plugins`: plugin manager, manifest parser, sandbox utilities.
- `spectrallibrary.ui`: PySide6 widgets, view models, resource management.
- `spectrallibrary.analytics`: optional algorithms (baseline correction, smoothing, peak detection).

### Import preview to viewer hand-off

1. `ImportWizardView` executes the importer via `ImportService.import_with_result`, emitting the persisted `ImportSummary` and the in-memory `ImportResult`.
2. The view raises an `import_records_ready` signal with the normalized `SpectrumRecord` list as soon as parsing completes.
3. `MainWindow` listens for this signal, caches the records, and surfaces a temporary "View imported spectra" shortcut in the status bar.
4. When analysts activate the shortcut, the window switches to `SpectrumViewerView` and calls `show_import_preview(records)`, populating metadata, sample counts, and the version list.
5. After launch the shortcut auto-hides (timer or manual click) until another import provides fresh records, keeping the UI focused yet discoverable.

This workflow avoids re-reading source files, keeps previews consistent between the dialog and viewer, and gives QA teams a single click to review spectra immediately after ingestion.

## Spectral format strategy

| Instrument / Source | Native formats | Import plan | Export plan |
| --- | --- | --- | --- |
| ASD FieldSpec / TerraSpec | `.asd` (binary), `.sig`, ASCII `.txt` | Phase 1: parse `SIG` / ASCII with existing CSV pipeline; Phase 2: add native `.asd` reader via vendor SDK or `asdfiles`. | CSV baseline; Phase 2: allow `.sig` export for round-trip with field tools. |
| ENVI spectral library | `.hdr` + `.sli` / `.dat` | Phase 3: use `spectral` or GDAL loader, handle paired files and metadata. | Provide ENVI-compatible export (`.hdr` + `.dat`) with optional resampling. |
| SVC HR / GER / Ocean Optics | `.sig`, `.spc`, instrument-specific ASCII | Phase 4: prioritize formats based on user demand; adapters reuse shared ASCII parsing helpers. | CSV + native ASCII mirrors where feasible. |
| Public libraries (USGS SPLib, ECOSTRESS, SPECCHIO) | `.splib`, `.h5`, API endpoints | Phase 5: build dedicated loaders or connectors; consider server sync. | Allow exports to open formats (HDF5, CSV) and direct API bundles. |

Key architectural notes:

- **Importer plugins** remain discoverable via `importer_registry`; new modules register themselves and share normalization helpers (unit conversion, wavelength alignment, QA flags).
- `ImportContext.extra_options` will provide instrument-specific toggles (dark-current subtraction, reflectance conversion, channel trimming).
- The preview dialog detects the selected importer to present instrument metadata (instrument model, integration time, calibration status) alongside sample rows, now with post-import access from the status panel.
- Analysts can copy detailed spectrum summaries or export a CSV for the selected record directly from the preview dialog, keeping quick QA workflows in the desktop app.
- Bulk export gathers all previewed spectra into a single CSV so the QA team can archive snapshots or re-run imports without hunting for the original files.
- `ImportService.import_with_result` returns the persisted summary plus the normalized `ImportResult`, allowing the UI to reopen the latest import without re-reading the source file.
- Export subsystem will expose a format selector in the UI and CLI. Exporters reuse the same registry pattern so third parties can add formats.
- Source fingerprinting (`source_files` table) stores original format so round-trip exports can include provenance and instrument settings.

Implementation roadmap:

1. Ship ASCII/`SIG` importer for ASD-style devices (minimal dependency footprint).
2. Extend exporter UI with a format dropdown and hook in CSV + SIG writers.
3. Introduce optional `spectral` dependency to read/write ENVI libraries; add tests with sample `.hdr` fixtures.
4. Iterate on additional instruments based on field team feedback; document requirements for submitting new sample files.
5. Provide command-line `spectrallibrary convert` tool for batch format conversion leveraging the importer/exporter registries.

Testing & QA strategy:

- Maintain lightweight fixture files per format (binary examples stored under `tests/fixtures` or generated on the fly to avoid repository bloat).
- Add importer unit tests asserting metadata normalization, unit conversions, and warning handling for malformed inputs.
- Extend integration tests to cover preview UI rendering and export workflows, ensuring round-trip fidelity.
- Verify clipboard and CSV export affordances from the import preview dialog with automated smoke tests plus manual QA notes.
- Capture manual QA checklists for domain experts (instrument metadata verification, reflectance consistency) before releasing new format support.

Export UX considerations:

- Library detail view and bulk export dialog expose a “Format” selector populated from the exporter registry (CSV, SIG, ENVI, etc.).
- Default option stays CSV; last-used preference persists per user.
- Preview panel summarizes expected file bundle (single file vs. header/data pair) and warns about instrument-specific requirements (e.g., ENVI needing `.hdr` and `.dat`).
- CLI gains `--format` and `--target` arguments so automations can request specific outputs without the UI.

## Data storage
- SQLite with WAL mode for concurrency; FTS5 for text search tables.
- Tables for materials, spectra, spectrum_points, tags, relationships, audit logs, plugin metadata.
	- `materials`: `id`, `library_name`, `material_name`, `category`, `location`, `comments`, timestamps.
	- `spectra`: `id`, `material_id`, `source` (instrument), `wavelength_unit`, `reflectance_unit`, `acquisition_date`, `quality_status`, provenance references (`source_file_id`, `plugin_id`).
	- `spectrum_points`: `spectrum_id`, `wavelength`, `reflectance`, optional uncertainty columns; arrays imported must retain positional integrity.
	- `source_files`: original filename, format, hash, importer metadata.
	- Support tables: tag mappings, version history, change logs.
- Optional DuckDB integration for heavy analytical workloads (read-only mirror of curated datasets).

## Plugin lifecycle
1. Discover manifests in `plugins/` and user-specific directories.
2. Validate compatibility and requested privileges.
3. Load plugin module in constrained namespace, instantiate entry point class.
4. Provide `AppContext` with read/write services, logging, and event bus access.
5. Activate contributions (menus, importers, tasks); monitor for errors.
6. Support hot reload (disable/enable) and safe deactivation on shutdown.

## Cross-cutting concerns
- **Logging**: structured logging with rotation; user-facing log viewer.
- **Configuration**: typed settings persisted in JSON/TOML, editable via UI.
- **Internationalization**: Qt translation system (ts files), plugin-friendly.
- **Task execution**: background worker pool for long-running imports/analysis; progress notifications.
- **Testing**: unit tests (pytest), UI tests (pytest-qt), integration tests using temporary SQLite databases.
