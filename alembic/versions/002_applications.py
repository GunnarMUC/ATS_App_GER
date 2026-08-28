"""applications + generated_documents.application_id

Revision ID: 002
Revises: 001
Create Date: 2026-08-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("job_descriptions.id"), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_id"),
    )
    op.add_column(
        "generated_documents",
        sa.Column("application_id", sa.String(length=36), sa.ForeignKey("applications.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("generated_documents", "application_id")
    op.drop_table("applications")
