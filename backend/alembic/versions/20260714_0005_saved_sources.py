"""add saved candidate connector sources

Revision ID: 20260714_0005
Revises: 20260714_0004
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_0005"
down_revision: str | None = "20260714_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("source_key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id", "provider", "source_key", name="uq_candidate_source"),
    )
    op.create_index("ix_candidate_sources_owner_id", "candidate_sources", ["owner_id"])
    op.create_index("ix_candidate_sources_candidate_id", "candidate_sources", ["candidate_id"])
    op.create_index("ix_candidate_source_enabled", "candidate_sources", ["candidate_id", "is_enabled"])


def downgrade() -> None:
    op.drop_table("candidate_sources")
