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

## Data storage
- SQLite with WAL mode for concurrency; FTS5 for text search tables.
- Tables for materials, spectra, spectrum_points, tags, relationships, audit logs, plugin metadata.
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
