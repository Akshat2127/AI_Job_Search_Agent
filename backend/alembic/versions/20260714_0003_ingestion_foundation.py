"""add candidate-owned ingestion provenance

Revision ID: 20260714_0003
Revises: 8a8bf14544a8
Create Date: 2026-07-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260714_0003"
down_revision: str | None = "8a8bf14544a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("owner_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("candidate_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("canonical_url", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("dedupe_key", sa.String(length=64), nullable=True))
        batch_op.create_foreign_key("fk_jobs_owner", "users", ["owner_id"], ["id"], ondelete="CASCADE")
        batch_op.create_foreign_key(
            "fk_jobs_candidate", "candidate_profiles", ["candidate_id"], ["id"], ondelete="CASCADE"
        )
        batch_op.create_index("ix_jobs_owner_id", ["owner_id"])
        batch_op.create_index("ix_jobs_candidate_id", ["candidate_id"])
        batch_op.create_index("ix_jobs_dedupe_key", ["dedupe_key"])
        batch_op.drop_constraint("uq_job_identity", type_="unique")
        batch_op.create_unique_constraint(
            "uq_job_candidate_identity", ["candidate_id", "company", "title", "url"]
        )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("discovered_count", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ingestion_runs_owner_id", "ingestion_runs", ["owner_id"])
    op.create_index("ix_ingestion_runs_candidate_id", "ingestion_runs", ["candidate_id"])
    op.create_index("ix_ingestion_runs_provider", "ingestion_runs", ["provider"])
    op.create_index("ix_ingestion_runs_status", "ingestion_runs", ["status"])
    op.create_index("ix_ingestion_owner_started", "ingestion_runs", ["owner_id", "started_at"])

    op.create_table(
        "job_source_records",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("source_key", sa.String(length=255), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "candidate_id", "provider", "source_key", "external_id", name="uq_candidate_job_source_identity"
        ),
    )
    op.create_index("ix_job_source_records_owner_id", "job_source_records", ["owner_id"])
    op.create_index("ix_job_source_records_candidate_id", "job_source_records", ["candidate_id"])
    op.create_index("ix_job_source_records_job_id", "job_source_records", ["job_id"])
    op.create_index("ix_job_source_records_ingestion_run_id", "job_source_records", ["ingestion_run_id"])
    op.create_index("ix_job_source_records_provider", "job_source_records", ["provider"])
    op.create_index("ix_job_source_job_provider", "job_source_records", ["job_id", "provider"])


def downgrade() -> None:
    op.drop_table("job_source_records")
    op.drop_table("ingestion_runs")
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_constraint("uq_job_candidate_identity", type_="unique")
        batch_op.create_unique_constraint("uq_job_identity", ["company", "title", "url"])
        batch_op.drop_index("ix_jobs_dedupe_key")
        batch_op.drop_index("ix_jobs_candidate_id")
        batch_op.drop_index("ix_jobs_owner_id")
        batch_op.drop_constraint("fk_jobs_candidate", type_="foreignkey")
        batch_op.drop_constraint("fk_jobs_owner", type_="foreignkey")
        batch_op.drop_column("dedupe_key")
        batch_op.drop_column("canonical_url")
        batch_op.drop_column("candidate_id")
        batch_op.drop_column("owner_id")
