from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base
from backend.app.models.identity import utc_now, uuid_string


class CandidateSource(Base):
    __tablename__ = "candidate_sources"
    __table_args__ = (
        UniqueConstraint("candidate_id", "provider", "source_key", name="uq_candidate_source"),
        Index("ix_candidate_source_enabled", "candidate_id", "is_enabled"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(50))
    source_key: Mapped[str] = mapped_column(String(100))
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (Index("ix_ingestion_owner_started", "owner_id", "started_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    source_key: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="running", index=True)
    discovered_count: Mapped[int] = mapped_column(Integer, default=0)
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobSourceRecord(Base):
    __tablename__ = "job_source_records"
    __table_args__ = (
        UniqueConstraint(
            "candidate_id", "provider", "source_key", "external_id", name="uq_candidate_job_source_identity"
        ),
        Index("ix_job_source_job_provider", "job_id", "provider"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    ingestion_run_id: Mapped[str] = mapped_column(ForeignKey("ingestion_runs.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    source_key: Mapped[str] = mapped_column(String(255))
    external_id: Mapped[str] = mapped_column(String(512))
    source_url: Mapped[str] = mapped_column(Text)
    canonical_url: Mapped[str] = mapped_column(Text)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
