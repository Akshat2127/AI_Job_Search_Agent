from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.session import Base
from backend.app.models.identity import utc_now, uuid_string

if TYPE_CHECKING:
    from backend.app.models.identity import User


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    __table_args__ = (UniqueConstraint("owner_id", "display_name", name="uq_candidate_owner_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    headline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    owner: Mapped[User] = relationship(back_populates="candidates")
    preference: Mapped[CandidatePreference | None] = relationship(
        back_populates="candidate", cascade="all, delete-orphan", uselist=False
    )
    skills: Mapped[list[CandidateSkill]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    experiences: Mapped[list[EmploymentExperience]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    answers: Mapped[list[ApplicationAnswer]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    resumes: Mapped[list[Resume]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class CandidatePreference(Base):
    __tablename__ = "candidate_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), unique=True)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[list[str]] = mapped_column(JSON, default=list)
    remote_preferences: Mapped[list[str]] = mapped_column(JSON, default=list)
    salary_floor: Mapped[float | None] = mapped_column(Float, nullable=True)
    excluded_employers: Mapped[list[str]] = mapped_column(JSON, default=list)
    excluded_titles: Mapped[list[str]] = mapped_column(JSON, default=list)
    keyword_preferences: Mapped[list[str]] = mapped_column(JSON, default=list)
    work_authorization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sponsorship_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    candidate: Mapped[CandidateProfile] = relationship(back_populates="preference")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    __table_args__ = (UniqueConstraint("candidate_id", "normalized_name", name="uq_candidate_skill"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str] = mapped_column(String(255))
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="user", nullable=False)

    candidate: Mapped[CandidateProfile] = relationship(back_populates="skills")


class EmploymentExperience(Base):
    __tablename__ = "employment_experiences"
    __table_args__ = (Index("ix_employment_candidate_dates", "candidate_id", "start_date", "end_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    employer: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    candidate: Mapped[CandidateProfile] = relationship(back_populates="experiences")


class ApplicationAnswer(Base):
    __tablename__ = "application_answers"
    __table_args__ = (UniqueConstraint("candidate_id", "question_key", name="uq_candidate_answer_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    question_key: Mapped[str] = mapped_column(String(100))
    answer: Mapped[str] = mapped_column(Text)
    sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    require_confirmation_each_time: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    candidate: Mapped[CandidateProfile] = relationship(back_populates="answers")


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidate_profiles.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(1024), unique=True)
    media_type: Mapped[str] = mapped_column(String(100))
    byte_size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    extracted_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    review_status: Mapped[str] = mapped_column(String(30), default="needs_review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    candidate: Mapped[CandidateProfile] = relationship(back_populates="resumes")
