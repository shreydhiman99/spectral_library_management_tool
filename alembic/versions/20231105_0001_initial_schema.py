"""Initial database schema.

Revision ID: 20231105_0001
Revises: 
Create Date: 2025-11-05 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20231105_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("library_name", sa.String(length=100), nullable=False),
        sa.Column("material_name", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("library_name", "material_name", name="uq_material_library_name_material_name"),
    )

    op.create_table(
        "source_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("original_name", sa.String(length=255), nullable=False),
        sa.Column("format", sa.String(length=50), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("importer_plugin", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="success"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("sha256", name="uq_source_files_sha256"),
    )

    op.create_table(
        "spectra",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_file_id", sa.Integer(), sa.ForeignKey("source_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("wavelength_unit", sa.String(length=20), nullable=False),
        sa.Column("reflectance_unit", sa.String(length=20), nullable=False),
        sa.Column("acquisition_date", sa.Date(), nullable=True),
        sa.Column("quality_status", sa.String(length=30), nullable=False, server_default="complete"),
        sa.Column("plugin_id", sa.String(length=120), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "spectrum_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("spectrum_id", sa.Integer(), sa.ForeignKey("spectra.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("wavelength", sa.Float(), nullable=False),
        sa.Column("reflectance", sa.Float(), nullable=False),
        sa.Column("uncertainty", sa.Float(), nullable=True),
        sa.UniqueConstraint("spectrum_id", "order_index", name="uq_spectrum_points_order"),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("name", name="uq_tags_name"),
    )

    op.create_table(
        "spectrum_tags",
        sa.Column("spectrum_id", sa.Integer(), sa.ForeignKey("spectra.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("spectrum_id", "tag_id", name="uq_spectrum_tag"),
    )

    op.create_table(
        "spectrum_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("spectrum_id", sa.Integer(), sa.ForeignKey("spectra.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reason", sa.String(length=120), nullable=True),
        sa.Column("metadata_snapshot", sa.JSON(), nullable=False),
        sa.UniqueConstraint("spectrum_id", "version_number", name="uq_spectrum_version"),
    )

    op.create_table(
        "change_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("user", sa.String(length=120), nullable=True),
        sa.Column("plugin_id", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("change_log")
    op.drop_table("spectrum_versions")
    op.drop_table("spectrum_tags")
    op.drop_table("tags")
    op.drop_table("spectrum_points")
    op.drop_table("spectra")
    op.drop_table("source_files")
    op.drop_table("materials")
