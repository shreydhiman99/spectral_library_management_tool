"""Domain services for presenting library hierarchy data."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import logging
from typing import Iterable, List, Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from ..db.models import Material, Spectrum
from ..db.session import get_session


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SpectrumNode:
    """Lightweight descriptor for spectrum entries in the tree."""

    id: int
    label: str
    source: str
    acquisition_date: date | None
    quality_status: str


@dataclass(frozen=True, slots=True)
class MaterialNode:
    """Material entry including its spectra."""

    id: int
    name: str
    category: str
    spectra: Sequence[SpectrumNode]


@dataclass(frozen=True, slots=True)
class LibraryNode:
    """Top-level library grouping."""

    name: str
    materials: Sequence[MaterialNode]


LibraryTree = Sequence[LibraryNode]


class LibraryBrowserService:
    """Compose library/material/spectrum data for the UI."""

    def __init__(self) -> None:
        # The service is stateless; session lifecycle is managed per call.
        pass

    def fetch_library_tree(self) -> LibraryTree:
        """Return a hierarchical representation of available materials and spectra."""

        try:
            with get_session() as session:
                materials: List[Material] = (
                    session.execute(
                        select(Material)
                        .options(joinedload(Material.spectra))
                        .order_by(Material.library_name, Material.material_name)
                    )
                    .unique()
                    .scalars()
                    .all()
                )
        except SQLAlchemyError as exc:  # pragma: no cover - defensive fallback
            logger.debug("Failed to fetch library tree: %s", exc)
            return ()

        grouped: Mapping[str, List[MaterialNode]] = defaultdict(list)
        for material in materials:
            node = MaterialNode(
                id=material.id,
                name=material.material_name,
                category=material.category,
                spectra=tuple(_build_spectrum_nodes(material.spectra)),
            )
            grouped[material.library_name].append(node)

        libraries: List[LibraryNode] = [
            LibraryNode(name=name, materials=tuple(materials))
            for name, materials in sorted(grouped.items())
        ]
        return tuple(libraries)


def _build_spectrum_nodes(spectra: Iterable[Spectrum]) -> Iterable[SpectrumNode]:
    for spectrum in sorted(
        spectra,
        key=lambda s: (
            s.acquisition_date is None,
            s.acquisition_date or date.min,
            s.id,
        ),
    ):
        label = _format_spectrum_label(spectrum)
        yield SpectrumNode(
            id=spectrum.id,
            label=label,
            source=spectrum.source,
            acquisition_date=spectrum.acquisition_date,
            quality_status=spectrum.quality_status,
        )


def _format_spectrum_label(spectrum: Spectrum) -> str:
    if spectrum.acquisition_date:
        return f"{spectrum.source} · {spectrum.acquisition_date.isoformat()}"
    return f"{spectrum.source} · #{spectrum.id}"
