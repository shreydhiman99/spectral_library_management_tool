# Spectral Library Desktop Application

An offline, cross-platform desktop tool for managing, visualizing, and exporting spectral libraries. The application targets laboratory and field teams who need a reliable spectral bank without relying on cloud services.

## Highlights
- **Multi-format ingestion**: Import spectra from CSV and ASD SIG/TXT exports with pluggable parsers.
- **Unified storage**: Normalize and persist materials and spectra in a SQLite database with provenance and version history.
- **Powerful search & filtering**: Full-text and faceted search across materials, metadata, and spectral characteristics.
- **Interactive visualization**: Overlay spectra, zoom, highlight peaks, and compare versions with PySide6-based UI components.
- **Plugin ecosystem**: Extend importers, analytics, visual panels, and automation hooks via a first-class plugin SDK.
- **Offline-first packaging**: Distribute as standalone installers for Windows, macOS, and Linux with optional DuckDB analytics add-ons.

## Project structure
```
├── data-samples/         # Example spectra and fixtures for testing
├── docs/                 # Requirements, architecture, and design documentation
├── plugins/              # Bundled or example plugins (development workspace)
├── src/spectrallibrary/  # Application source code
├── tests/                # Automated tests
└── pyproject.toml        # Project metadata and dependencies (Poetry)
```

## Roadmap snapshot
| Phase | Timeline (est.) | Focus |
| --- | --- | --- |
| 0 | Weeks 0-2 | Project ignition, requirements baseline, tooling setup |
| 1 | Weeks 2-6 | Database schema, core services, import/export interfaces |
| 2 | Weeks 6-10 | PySide6 shell, task system, import wizard |
| 3 | Weeks 10-16 | Library management UI, visualization, export workflows |
| 4 | Weeks 16-22 | Plugin platform v1, SDK, extension samples |
| 5 | Weeks 22-28 | Analytics, enrichment, metadata quality tooling |
| 6 | Weeks 28-32 | Packaging & distribution (installers, docs) |
| 7 | Weeks 32-36 | Stabilization, launch readiness, support assets |

## Getting started
### Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency and virtual environment management

### Setup
```powershell
# Clone the repository and enter the workspace
git clone <repo-url> spectral-library
cd spectral-library

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell

# Apply the latest database migrations
poetry run alembic upgrade head

# (Optional) Load demo content for the UI preview
poetry run spectrallibrary-seed

# Run placeholder test suite
poetry run pytest
```

### Preview the UI shell
```powershell
# Ensure the virtual environment is active (via `poetry shell` or `poetry run`)
poetry run python -m spectrallibrary.app
```

If you are running on a headless system, set `QT_QPA_PLATFORM=offscreen` before
launching to avoid Qt display errors.

The navigation tree pulls live data from the database. Running the demo seed
command beforehand ensures the preview showcases populated libraries and
materials.

### Sample CSV for importer

Use `data-samples/demo_import.csv` or `data-samples/demo_import_extended.csv`
with the Import Wizard (or CLI) to exercise the CSV ingestion workflow. The
extended version includes repeat measurements, lab archives, and reference
panels to showcase deduplication and metadata overrides.

Launch the import wizard and choose **Preview mapping** to inspect the parsed
records (first ten rows) and any validation warnings before running the full
import.

After an import completes, the status panel now includes a **View imported
records…** shortcut. It reopens the same preview dialog with the persisted
data, so you can confirm metadata and inspect wavelength/reflectance values
without re-running the import. Within the dialog you can copy the detailed
summary to the clipboard or export the selected spectrum to CSV for quick
sharing.

If a file contains only invalid rows, the import still completes and surfaces
warnings without creating new spectra, so you can fix issues and retry safely.

ASD FieldSpec ASCII (`.sig` / exported `.txt`) files are also supported—choose
them in the import dialog to normalize field spectra directly into the library.
Sample files live under `data-samples/asd/` for quick demonstrations (reflectance
and radiance variants).

### Recent updates
- Import preview dialog shows wavelength ranges, reflectance samples, and a
	detailed inspector for up to ten records.
- Completed imports surface a **View imported records…** button so analysts can
	reopen the preview for the latest run.
- Copy spectrum details to the clipboard or export the selected record to CSV
	straight from the preview dialog.
- Export all previewed records to a single CSV in one click for bulk QA or
	re-import scenarios.

## Documentation index
- `docs/requirements.md` – functional and non-functional requirements
- `docs/architecture-overview.md` – layered architecture, plugin interfaces, data model
- `docs/setup.md` – environment preparation and platform-specific notes
- `docs/roadmap.md` – detailed milestone breakdown and acceptance criteria
- `docs/import-mapping.md` – CSV column expectations for the importer
- `docs/importers/asd_ascii.md` – design notes for the ASD ASCII/SIG importer

## Contributing
1. Enable pre-commit hooks (`poetry run pre-commit install`).
2. Create feature branches from `main` following the defined naming convention (e.g., `feature/<scope>`).
3. Ensure linting, typing, and tests pass before opening a pull request.
4. Update documentation for user-facing or architectural changes.

## License
Released under the MIT License. See `LICENSE` for details (to be added).
