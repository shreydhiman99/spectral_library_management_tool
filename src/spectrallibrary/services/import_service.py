"""Application service for orchestrating imports."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from sqlalchemy import select

from ..db.models import Material, SourceFile, Spectrum, SpectrumPoint, Tag
from ..db.session import get_session
from ..importing import ImportContext, ImportResult, SpectrumRecord, importer_registry


@dataclass(frozen=True, slots=True)
class ImportSummary:
    """Summary information returned after an import operation."""

    created_materials: int
    created_spectra: int
    warnings: Sequence[str]


class ImportService:
    """Load files via importers and persist the resulting records."""

    def __init__(self) -> None:
        self._registry = importer_registry

    def import_path(
        self,
        path: Path,
        *,
        context: ImportContext | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> ImportSummary:
        summary, _ = self._import_impl(
            path,
            context=context,
            progress_callback=progress_callback,
            collect_result=False,
        )
        return summary

    def import_with_result(
        self,
        path: Path,
        *,
        context: ImportContext | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> tuple[ImportSummary, ImportResult]:
        summary, result = self._import_impl(
            path,
            context=context,
            progress_callback=progress_callback,
            collect_result=True,
        )
        assert result is not None  # noqa: S101 - defensive; collect_result guarantees value
        return summary, result

    def _import_impl(
        self,
        path: Path,
        *,
        context: ImportContext | None,
        progress_callback: Callable[[int, int], None] | None,
        collect_result: bool,
    ) -> tuple[ImportSummary, ImportResult | None]:
        result = self._registry.import_file(path, context=context)
        created_materials = 0
        created_spectra = 0
        total_records = len(result.records)
        processed_records = 0

        if progress_callback:
            progress_callback(processed_records, total_records)

        with get_session() as session:
            source_file = self._get_or_create_source_file(session, path)
            tag_cache: dict[str, Tag] = {}

            for record in result.records:
                material, material_created = self._get_or_create_material(session, record)
                if material_created:
                    created_materials += 1

                spectrum = Spectrum(
                    material=material,
                    source_file=source_file,
                    source=record.source,
                    wavelength_unit=record.wavelength_unit,
                    reflectance_unit=record.reflectance_unit,
                    acquisition_date=record.acquisition_date,
                    quality_status="complete",
                    comments=record.comments,
                )

                spectrum.points = _build_points(record)
                self._apply_tags(session, spectrum, record.tags, tag_cache)
                session.add(spectrum)
                created_spectra += 1
                processed_records += 1

                if progress_callback:
                    progress_callback(processed_records, total_records)

        summary = ImportSummary(
            created_materials=created_materials,
            created_spectra=created_spectra,
            warnings=tuple(result.warnings),
        )

        return summary, result if collect_result else None

    # ------------------------------------------------------------------
    # ORM helpers

    def _get_or_create_material(self, session, record: SpectrumRecord) -> tuple[Material, bool]:
        material = session.execute(
            select(Material)
            .where(
                Material.library_name == record.library_name,
                Material.material_name == record.material_name,
            )
        ).scalar_one_or_none()

        created = False
        if material is None:
            material = Material(
                library_name=record.library_name,
                material_name=record.material_name,
                category=record.category,
                location=record.location,
                comments=record.comments,
            )
            session.add(material)
            created = True
        else:
            # update metadata if new info is provided
            material.category = record.category
            if record.location:
                material.location = record.location
            if record.comments:
                material.comments = record.comments

        return material, created

    def _get_or_create_source_file(self, session, path: Path) -> SourceFile:
        sha256 = _hash_file(path)
        source_file = session.execute(
            select(SourceFile).where(SourceFile.sha256 == sha256)
        ).scalar_one_or_none()
        if source_file is None:
            source_file = SourceFile(
                original_name=path.name,
                format=path.suffix.lstrip(".").lower() or "csv",
                sha256=sha256,
                importer_plugin="csv",
                status="success",
            )
            session.add(source_file)
        return source_file

    def _apply_tags(
        self,
        session,
        spectrum: Spectrum,
        tags: Iterable[str],
        tag_cache: dict[str, Tag],
    ) -> None:
        for tag_name in tags:
            normalized = tag_name.strip()
            if not normalized:
                continue
            if normalized in tag_cache:
                spectrum.tags.append(tag_cache[normalized])
                continue

            tag = session.execute(select(Tag).where(Tag.name == normalized)).scalar_one_or_none()
            if tag is None:
                tag = Tag(name=normalized)
                session.add(tag)
                session.flush([tag])
            tag_cache[normalized] = tag
            spectrum.tags.append(tag)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _build_points(record: SpectrumRecord) -> list[SpectrumPoint]:
    return [
        SpectrumPoint(
            order_index=index,
            wavelength=wavelength,
            reflectance=reflectance,
        )
        for index, (wavelength, reflectance) in enumerate(
            zip(record.wavelengths, record.reflectance), start=1
        )
    ]
