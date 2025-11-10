"""Populate the local database with demo content for UI previews."""

from __future__ import annotations

from datetime import date
from typing import Iterable, Sequence

from sqlalchemy import delete, select

from .db.models import Material, Spectrum, SpectrumPoint
from .db.session import get_session


def seed_demo_data(*, force: bool = False) -> int:
    """Insert a small demo dataset.

    Args:
        force: When ``True`` existing materials will be ignored and demo data
            will be inserted even if rows already exist.

    Returns:
        Number of materials created.
    """

    with get_session() as session:
        existing_materials = session.execute(select(Material.id)).first()
        if existing_materials is not None and not force:
            return 0

        if force and existing_materials is not None:
            session.execute(delete(SpectrumPoint))
            session.execute(delete(Spectrum))
            session.execute(delete(Material))

        _create_demo_materials(session)

    return len(_DEMO_DATA)


def _create_demo_materials(session) -> None:
    for material_payload in _DEMO_DATA:
        material = Material(
            library_name=material_payload["library_name"],
            material_name=material_payload["material_name"],
            category=material_payload["category"],
            location=material_payload.get("location"),
            comments=material_payload.get("comments"),
        )

        for spec_payload in material_payload["spectra"]:
            spectrum = Spectrum(
                source=spec_payload["source"],
                wavelength_unit=spec_payload["wavelength_unit"],
                reflectance_unit=spec_payload["reflectance_unit"],
                acquisition_date=spec_payload.get("acquisition_date"),
                quality_status=spec_payload.get("quality_status", "complete"),
                comments=spec_payload.get("comments"),
            )
            spectrum.points = [
                SpectrumPoint(
                    order_index=index,
                    wavelength=wavelength,
                    reflectance=reflectance,
                    uncertainty=None,
                )
                for index, (wavelength, reflectance) in enumerate(spec_payload["series"], start=1)
            ]
            material.spectra.append(spectrum)

        session.add(material)


def _sample_series(start: float, end: float, *, steps: int) -> Iterable[tuple[float, float]]:
    """Generate a simple linear ramp between two reflectance values."""

    if steps < 2:
        raise ValueError("steps must be >= 2")

    wavelength_start = 400.0
    wavelength_step = 50.0

    reflectance_step = (end - start) / (steps - 1)
    for index in range(steps):
        yield (wavelength_start + wavelength_step * index, start + reflectance_step * index)


_DEMO_DATA: Sequence[dict[str, object]] = (
    {
        "library_name": "Global Reference",
        "material_name": "Basalt-01",
        "category": "Igneous",
        "location": "Iceland",
        "spectra": (
            {
                "source": "ASD FieldSpec 4",
                "wavelength_unit": "nm",
                "reflectance_unit": "fraction",
                "acquisition_date": date(2024, 3, 14),
                "series": _sample_series(0.12, 0.43, steps=5),
            },
            {
                "source": "ASD FieldSpec 4",
                "wavelength_unit": "nm",
                "reflectance_unit": "fraction",
                "acquisition_date": date(2024, 4, 2),
                "series": _sample_series(0.15, 0.40, steps=5),
            },
        ),
    },
    {
        "library_name": "Global Reference",
        "material_name": "Sandstone-01",
        "category": "Sedimentary",
        "spectra": (
            {
                "source": "ASD TerraSpec",
                "wavelength_unit": "nm",
                "reflectance_unit": "fraction",
                "acquisition_date": date(2024, 6, 11),
                "series": _sample_series(0.22, 0.55, steps=5),
            },
        ),
    },
    {
        "library_name": "Field Campaign 2024",
        "material_name": "Ice Core A",
        "category": "Cryogenic",
        "location": "Greenland",
        "spectra": (),
    },
)


def main() -> None:  # pragma: no cover - CLI convenience
    created = seed_demo_data()
    if created:
        print(f"Seeded {created} demo materials.")
    else:
        print("Database already contained materials; skipping demo seed.")


if __name__ == "__main__":  # pragma: no cover - CLI convenience
    main()
