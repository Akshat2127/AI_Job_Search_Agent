from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


def legacy_utc_now() -> datetime:
    """Return naive UTC until the legacy jobs timestamps receive a data migration."""
    return datetime.now(UTC).replace(tzinfo=None)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("candidate_id", "company", "title", "url", name="uq_job_candidate_identity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    candidate_id: Mapped[str | None] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    company: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    url: Mapped[str] = mapped_column(Text)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    fit_score: Mapped[int] = mapped_column(Integer, default=0)
    score_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_variant: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    recruiter_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(String(30), default="new")
    status: Mapped[str] = mapped_column(String(30), default="discovered")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=legacy_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=legacy_utc_now, onupdate=legacy_utc_now)
