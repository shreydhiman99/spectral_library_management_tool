# ASD ASCII / SIG Importer Design

## Format overview

- **File extensions**: `.sig`, `.txt`, `.asd` ASCII export.
- **Encoding**: Typically UTF-8 or ANSI; includes header section and tab-delimited data.
- **Header metadata**: instrument model, serial number, integration time, scan settings, units (Radiance, Reflectance), wavelength range.
- **Data section**: columns for wavelength, sample radiance, reference radiance, reflectance (depends on export options).
- **Variants**: Some exports include comment blocks starting with `>` or `[Header]` sections; others follow a simple key-value list before numeric data.

## Parsing requirements

- Skip or capture header lines until the numeric table begins.
- Detect column order; common layout:
  1. Wavelength (nm)
  2. Sample Radiance (W/sr/m²/nm)
  3. Reference Radiance (optional)
  4. Reflectance (ratio) — may be absent if radiance-only export.
- Fallback tags/metadata: instrument model, integration time, averaging, operator name.
- Units:
  - If reflectance column present, set `reflectance_unit = "ratio"`.
  - Otherwise, set `reflectance_unit = "radiance"` and flag missing reflectance.
- Library/material fields come from `ImportContext` overrides or header hints (e.g., `Target Name`).

## SpectrumRecord mapping

| SpectrumRecord field | Source |
| --- | --- |
| `library_name` | `context.target_library` or header `Library`/`Project`; default to "ASD Imports". |
| `material_name` | Header `Sample`/`Target` or file stem. |
| `category` | Header `Category` or default "Field". |
| `source` | Instrument model (e.g., `ASD FieldSpec 4`) + integration settings. |
| `wavelength_unit` | Usually `nm`. |
| `reflectance_unit` | `ratio` if column present, otherwise `radiance`. |
| `wavelengths` | First numeric column. |
| `reflectance` | Prefer reflectance column; if absent, use sample radiance but add warning. |
| `metadata` | Remaining header key/values (integration time, averages, operator, GPS). |
| `tags` | Include `"asd"`, instrument model, and quality flags if present. |

## Context options

Extend `ImportContext.extra_options` to accept:

- `material_name`: override per-file material name.
- `treat_radiance_as_reflectance`: bool – if true, importer stores radiance values as-is but marks metadata.
- `column_map`: optional dict to specify column indices (for non-standard exports).

## Warnings

- Warn when reflectance column missing (suggest converting in FieldSpec software).
- Warn if wavelength spacing inconsistent (e.g., truncated scan).
- Warn when header units unknown.
- If any numeric row fails to parse, skip and log row number.

## Registration

Create `src/spectrallibrary/importing/asd_ascii_importer.py` with:

- `formats = ("sig", "txt")`
- `can_handle`: check suffix and presence of ASD header markers (`"[Instrument]"`, `"SpectraVista"`, etc.).
- `load`: parse header/data, build `SpectrumRecord`, append warnings.
- Register via `register_importer(AsdAsciiImporter())`.

## Sample data

- Collect anonymized `.sig` exported as reflectance.
- Create synthetic fixture with radiance-only variant.
- Store under `tests/fixtures/asd/` and ensure small (<50 lines).

## Tests

- Validate reflectance import: correct units, wavelengths count, metadata captured.
- Validate radiance-only import: warning emitted, reflectance_unit = `radiance`.
- Validate column map override.
- Ensure importer ignored for non-ASD `.txt` (delegate to CSV importer).
