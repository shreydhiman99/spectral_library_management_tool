# Spectral Library Desktop Application

An offline, cross-platform desktop tool for managing, visualizing, and exporting spectral libraries. The application targets laboratory and field teams who need a reliable spectral bank without relying on cloud services.

## Highlights
- **Multi-format ingestion**: Import spectra from CSV, TXT, XLSX, and JSON files with pluggable parsers.
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

# Run placeholder test suite
poetry run pytest
```

## Documentation index
- `docs/requirements.md` – functional and non-functional requirements
- `docs/architecture-overview.md` – layered architecture, plugin interfaces, data model
- `docs/setup.md` – environment preparation and platform-specific notes
- `docs/roadmap.md` – detailed milestone breakdown and acceptance criteria

## Contributing
1. Enable pre-commit hooks (`poetry run pre-commit install`).
2. Create feature branches from `main` following the defined naming convention (e.g., `feature/<scope>`).
3. Ensure linting, typing, and tests pass before opening a pull request.
4. Update documentation for user-facing or architectural changes.

## License
Released under the MIT License. See `LICENSE` for details (to be added).
