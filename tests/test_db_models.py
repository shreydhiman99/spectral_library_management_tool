"""Basic tests for database infrastructure and ORM mappings."""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import create_engine

from spectrallibrary.db import Base, configure_engine, get_session
from spectrallibrary.db.models import Material, Spectrum, SpectrumPoint, Tag


@pytest.fixture()
def in_memory_db():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    configure_engine(engine)
    yield engine
    Base.metadata.drop_all(engine)


def test_material_spectrum_relationship(in_memory_db):
    wavelengths = [350.0, 351.0, 352.0]
    reflectance = [0.08, 0.085, 0.09]

    with get_session() as session:
        material = Material(
            library_name="USGS",
            material_name="Basalt",
            category="Igneous Rock",
            location="Utah, USA",
        )
        session.add(material)
        session.flush()

        spectrum = Spectrum(
            material_id=material.id,
            source="ASD FieldSpec 4",
            wavelength_unit="nm",
            reflectance_unit="fraction",
            acquisition_date=date(2019, 7, 15),
        )
        spectrum.points = [
            SpectrumPoint(order_index=i, wavelength=w, reflectance=r)
            for i, (w, r) in enumerate(zip(wavelengths, reflectance))
        ]

        tag = Tag(name="baseline")
        spectrum.tags.append(tag)
        material.spectra.append(spectrum)

    with get_session() as session:
        stored = session.query(Material).filter_by(material_name="Basalt").one()
        assert stored.spectra[0].points[0].wavelength == pytest.approx(350.0)
        assert stored.spectra[0].tags[0].name == "baseline"
