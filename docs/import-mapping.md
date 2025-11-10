# CSV Import Mapping

The CSV importer expects records normalized to the following columns. Additional
columns are captured as metadata key/value pairs and stored alongside each
spectrum.

| Column | Required | Description |
| --- | --- | --- |
| `library_name` | Yes* | Logical library/collection. Can be overridden via UI option. |
| `material_name` | Yes | Material identifier within the library. |
| `category` | Yes | Material category (e.g., Igneous, Sedimentary). |
| `source` | Yes | Instrument or acquisition descriptor. |
| `wavelength_unit` | Yes | Unit for wavelength axis (e.g., `nm`). |
| `reflectance_unit` | Yes | Unit for the reflectance axis (e.g., `fraction`). |
| `wavelengths` | Yes | Semicolon-separated float series for wavelengths. |
| `reflectance` | Yes | Semicolon-separated float series matching wavelengths. |
| `acquisition_date` | No | ISO-8601 date string (YYYY-MM-DD). |
| `location` | No | Free-text location description. |
| `comments` | No | Additional notes captured on the spectrum. |
| `tags` | No | Semicolon-separated list of tag names. |

## Example row

```
library_name,material_name,category,source,wavelength_unit,reflectance_unit,wavelengths,reflectance,acquisition_date,tags
Global Reference,Basalt-01,Igneous,ASD FieldSpec 4,nm,fraction,400;401;402,0.11;0.12;0.13,2024-03-14,baseline;approved
```

## Notes
- Series columns (`wavelengths`, `reflectance`) must contain the same number of
  values. The importer validates length equality.
- Unknown columns are preserved as metadata in the database for downstream
  processing.
- Tag names are created on the fly if they do not already exist in the catalog.
- When multiple rows map to the same library/material, the existing material is
  reused and metadata fields (category, location, comments) are updated if new
  values are provided.
- Rows that fail validation (missing required fields, unmatched series lengths,
  bad numeric values, etc.) are skipped and logged as warnings. If every row is
  invalid, the importer returns warnings with zero spectra created so you can
  correct the file and retry.
- Source file fingerprints (SHA-256) prevent duplicate ingestion metadata.
