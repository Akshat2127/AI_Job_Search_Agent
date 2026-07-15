from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.job import Job
from backend.app.schemas.job import JobCreate
from backend.app.services.drafts import build_cover_letter, build_recruiter_message
from backend.app.services.scoring import score_job


def create_job(db: Session, payload: JobCreate) -> Job:
    existing = db.execute(
        select(Job).where(
            Job.candidate_id.is_(None),
            Job.company == payload.company,
            Job.title == payload.title,
            Job.url == payload.url,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    job = Job(**payload.model_dump())
    enrich_job(job)
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.execute(
            select(Job).where(
                Job.candidate_id.is_(None),
                Job.company == payload.company,
                Job.title == payload.title,
                Job.url == payload.url,
            )
        ).scalar_one()
        return existing
    db.refresh(job)
    return job


def enrich_job(job: Job) -> Job:
    score, reason, variant = score_job(job)
    job.fit_score = score
    job.score_reason = reason
    job.resume_variant = variant
    job.cover_letter = build_cover_letter(job)
    job.recruiter_message = build_recruiter_message(job)
    return job


def list_jobs(
    db: Session, min_score: int | None = None, decision: str | None = None, q: str | None = None
) -> list[Job]:
    stmt = select(Job).where(Job.candidate_id.is_(None))
    if min_score is not None:
        stmt = stmt.where(Job.fit_score >= min_score)
    if decision:
        stmt = stmt.where(Job.decision == decision)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Job.title.ilike(like)) | (Job.company.ilike(like)) | (Job.description.ilike(like)))
    stmt = stmt.order_by(Job.fit_score.desc(), Job.created_at.desc())
    return list(db.execute(stmt).scalars())
