"""SQLAlchemy ORM models for the Spectral Library database."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Column,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TimestampMixin:
    """Adds created/updated timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Material(TimestampMixin, Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    library_name: Mapped[str] = mapped_column(String(100), nullable=False)
    material_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    spectra: Mapped[List["Spectrum"]] = relationship("Spectrum", back_populates="material", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("library_name", "material_name", name="uq_material_library_name_material_name"),
    )


class SourceFile(TimestampMixin, Base):
    __tablename__ = "source_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str] = mapped_column(String(50), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    importer_plugin: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="success", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    spectra: Mapped[List["Spectrum"]] = relationship("Spectrum", back_populates="source_file")


class Spectrum(TimestampMixin, Base):
    __tablename__ = "spectra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    source_file_id: Mapped[Optional[int]] = mapped_column(ForeignKey("source_files.id", ondelete="SET NULL"))

    source: Mapped[str] = mapped_column(String(120), nullable=False)
    wavelength_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    reflectance_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    quality_status: Mapped[str] = mapped_column(String(30), default="complete", nullable=False)
    plugin_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    material: Mapped[Material] = relationship("Material", back_populates="spectra")
    source_file: Mapped[Optional[SourceFile]] = relationship("SourceFile", back_populates="spectra")
    points: Mapped[List["SpectrumPoint"]] = relationship(
        "SpectrumPoint", order_by="SpectrumPoint.order_index", back_populates="spectrum", cascade="all, delete-orphan"
    )
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary="spectrum_tags", back_populates="spectra")
    versions: Mapped[List["SpectrumVersion"]] = relationship(
        "SpectrumVersion", back_populates="spectrum", cascade="all, delete-orphan"
    )


class SpectrumPoint(Base):
    __tablename__ = "spectrum_points"
    __table_args__ = (UniqueConstraint("spectrum_id", "order_index", name="uq_spectrum_points_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spectrum_id: Mapped[int] = mapped_column(ForeignKey("spectra.id", ondelete="CASCADE"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    wavelength: Mapped[float] = mapped_column(Float, nullable=False)
    reflectance: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    spectrum: Mapped[Spectrum] = relationship("Spectrum", back_populates="points")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    spectra: Mapped[List[Spectrum]] = relationship("Spectrum", secondary="spectrum_tags", back_populates="tags")


spectrum_tags = Table(
    "spectrum_tags",
    Base.metadata,
    Column("spectrum_id", ForeignKey("spectra.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("spectrum_id", "tag_id", name="uq_spectrum_tag"),
)


class SpectrumVersion(Base):
    __tablename__ = "spectrum_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spectrum_id: Mapped[int] = mapped_column(ForeignKey("spectra.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    metadata_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    spectrum: Mapped[Spectrum] = relationship("Spectrum", back_populates="versions")

    __table_args__ = (UniqueConstraint("spectrum_id", "version_number", name="uq_spectrum_version"),)


class ChangeLog(Base):
    __tablename__ = "change_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    user: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    plugin_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)


__all__ = [
    "Material",
    "SourceFile",
    "Spectrum",
    "SpectrumPoint",
    "Tag",
    "SpectrumVersion",
    "ChangeLog",
    "spectrum_tags",
]
