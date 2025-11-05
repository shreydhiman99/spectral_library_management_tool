# Requirements

## Functional
- **Data ingestion**
  - Import spectra from CSV, TXT, XLSX, JSON.
  - Map arbitrary column names to standardized fields.
  - Support batch imports with progress reporting and rollback on failure.
- **Data management**
  - Store materials and spectra with provenance, metadata, and version history.
  - Allow create/read/update/archive operations via UI and service layer.
  - Track incomplete metadata and provide review workflows.
  - Capture the following baseline metadata fields for every spectrum:
    - `library_name` (required): logical library or collection the spectrum belongs to.
    - `material_name` (required): primary material identifier, with alias support.
    - `category` (required): taxonomic grouping (e.g., "Igneous Rock").
    - `source` (required): instrument or acquisition system (e.g., "ASD FieldSpec 4").
    - `location` (optional): geographic or contextual origin (free-text + optional geo coordinates).
    - `wavelength_unit` (required): unit for wavelength axis (normalized to nm internally).
    - `reflectance_unit` (required): unit for response values (e.g., fraction, percentage).
    - `acquisition_date` (optional): ISO-8601 date of measurement.
    - `comments` (optional): free-form notes on acquisition context.
    - Spectral series data pairs (required): `wavelengths[]` and `reflectance[]` arrays of equal length.
- **Search & discovery**
  - Full-text search across material names, tags, notes.
  - Faceted filtering by category, instrument, date range, quality flags.
  - Quick comparison across multiple spectra.
- **Visualization**
  - Interactive plots (zoom, pan, overlays, peak markers).
  - Display metadata alongside spectra.
  - Export plots to PNG/SVG for reporting.
- **Export**
  - Export spectra/data subsets to CSV, TXT, XLSX, JSON with templates.
  - Include provenance metadata in exported files.
- **Plugins**
  - Discover and manage plugins with manifest-based activation.
  - Support plugin extensions for importers, analytics, visualization, automation hooks.
  - Provide SDK and documentation for third parties.

## Non-functional
- **Offline operation**: no external network dependencies at runtime.
- **Cross-platform**: Windows, macOS, Linux builds (x86_64 initially).
- **Performance**: Handle thousands of spectra per library while keeping UI responsive (<300 ms for common actions).
- **Security & privacy**: sandbox plugin permissions, maintain audit logs, optional signing for plugins/installers.
- **Reliability**: transactional imports, automated backups, data integrity checks.
- **Extensibility**: well-defined service interfaces, versioned plugin API, modular architecture.
- **Maintainability**: comprehensive tests, linting, type checks, documentation.

## Open questions
- Finalize exact metadata schema per organization (instrument parameters, environmental data).
- Decide on baseline analytics bundle vs. plugin-only delivery.
- Confirm packaging requirements for air-gapped deployments (code signing, offline docs, etc.).
