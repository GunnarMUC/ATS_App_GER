"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reference_cvs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("original_filename", sa.String(length=512), nullable=False),
        sa.Column("stored_path", sa.String(length=1024), nullable=False),
        sa.Column("media_type", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("structured_json", sa.JSON(), nullable=True),
        sa.Column("ats_structural_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ollama_host", sa.String(length=512), nullable=False),
        sa.Column("model_fast", sa.String(length=256), nullable=False),
        sa.Column("model_strong", sa.String(length=256), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "role_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("role_family", sa.String(length=64), nullable=False),
        sa.Column("lens_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "fact_locks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("reference_cv_id", sa.String(length=36), sa.ForeignKey("reference_cvs.id"), nullable=False),
        sa.Column("facts_json", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title_raw", sa.String(length=512), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("stored_path", sa.String(length=1024), nullable=True),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("analysis_json", sa.JSON(), nullable=True),
        sa.Column("generating", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "role_detections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("job_descriptions.id"), nullable=False),
        sa.Column("detection_json", sa.JSON(), nullable=False),
        sa.Column("user_role_family", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "adaptation_plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("job_descriptions.id"), nullable=False),
        sa.Column("fact_lock_id", sa.String(length=36), sa.ForeignKey("fact_locks.id"), nullable=False),
        sa.Column("role_profile_id", sa.String(length=36), sa.ForeignKey("role_profiles.id"), nullable=True),
        sa.Column("plan_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "generated_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("job_descriptions.id"), nullable=False),
        sa.Column("fact_lock_id", sa.String(length=36), sa.ForeignKey("fact_locks.id"), nullable=False),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("adaptation_plans.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("structured_json", sa.JSON(), nullable=True),
        sa.Column("docx_path", sa.String(length=1024), nullable=True),
        sa.Column("pdf_path", sa.String(length=1024), nullable=True),
        sa.Column("txt_path", sa.String(length=1024), nullable=True),
        sa.Column("fact_guard_passed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("generated_documents")
    op.drop_table("adaptation_plans")
    op.drop_table("role_detections")
    op.drop_table("job_descriptions")
    op.drop_table("fact_locks")
    op.drop_table("role_profiles")
    op.drop_table("app_settings")
    op.drop_table("reference_cvs")
