# Changelog

## 2025-11-10
- Import wizard now exposes a **View imported records…** action after each run, reusing the enhanced preview dialog.
- Preview dialog highlights wavelength ranges, reflectance samples, and a detail pane for quick QA.
- Added clipboard copy and CSV export options for the selected spectrum in the preview dialog.
- Preview dialog can now export all previewed spectra to a single CSV, making it easy to archive QA datasets.
- `ImportService` gained `import_with_result` so UI workflows can retain normalized records without re-reading files.
