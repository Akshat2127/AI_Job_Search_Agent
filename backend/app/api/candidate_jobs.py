import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.candidate import CandidateProfile
from backend.app.models.identity import User, utc_now
from backend.app.models.ingestion import CandidateSource, IngestionRun, JobSourceRecord
from backend.app.models.job import Job
from backend.app.schemas.ingestion import (
    CandidateSourceCreate,
    CandidateSourceOut,
    CandidateSourceUpdate,
    IngestionRunOut,
)
from backend.app.schemas.job import (
    CandidateDecisionUpdate,
    CandidateJobOut,
    CandidateJobPage,
    JobProvenanceOut,
    ManualJobCreate,
    ManualJobIntakeOut,
)
from backend.app.security.auth import get_current_user
from backend.app.services import candidates as candidate_service
from backend.app.services.ats_connectors import ExternalJob
from backend.app.services.audit import record_event
from backend.app.services.ingestion import (
    ConnectorExecutionFailed,
    canonicalize_manual_job_url,
    execute_connector,
    ingest_records,
)

router = APIRouter(prefix="/candidates/{candidate_id}", tags=["candidate jobs"])


def require_candidate(candidate_id: str, user: User, db: Session) -> CandidateProfile:
    candidate = candidate_service.owned_candidate(db, user, candidate_id)
    if candidate is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Candidate not found")
    return candidate


def require_source(candidate_id: str, source_id: str, user: User, db: Session) -> CandidateSource:
    source = db.execute(
        select(CandidateSource).where(
            CandidateSource.id == source_id,
            CandidateSource.candidate_id == candidate_id,
            CandidateSource.owner_id == user.id,
        )
    ).scalar_one_or_none()
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found")
    return source


@router.get("/sources", response_model=list[CandidateSourceOut])
def list_sources(
    candidate_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CandidateSource]:
    candidate = require_candidate(candidate_id, user, db)
    return list(
        db.execute(
            select(CandidateSource)
            .where(CandidateSource.owner_id == user.id, CandidateSource.candidate_id == candidate.id)
            .order_by(CandidateSource.created_at)
        ).scalars()
    )


@router.post("/sources", response_model=CandidateSourceOut, status_code=status.HTTP_201_CREATED)
def create_source(
    candidate_id: str,
    payload: CandidateSourceCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateSource:
    candidate = require_candidate(candidate_id, user, db)
    source = CandidateSource(owner_id=user.id, candidate_id=candidate.id, **payload.model_dump())
    db.add(source)
    try:
        db.flush()
        record_event(
            db,
            owner_id=user.id,
            candidate_id=candidate.id,
            action="source.created",
            entity_type="candidate_source",
            entity_id=source.id,
            metadata={"provider": source.provider},
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This source already exists") from error
    db.refresh(source)
    return source


@router.patch("/sources/{source_id}", response_model=CandidateSourceOut)
def update_source(
    candidate_id: str,
    source_id: str,
    payload: CandidateSourceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateSource:
    require_candidate(candidate_id, user, db)
    source = require_source(candidate_id, source_id, user, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    record_event(
        db,
        owner_id=user.id,
        candidate_id=candidate_id,
        action="source.updated",
        entity_type="candidate_source",
        entity_id=source.id,
        metadata={"is_enabled": source.is_enabled},
    )
    db.commit()
    db.refresh(source)
    return source


@router.post("/sources/{source_id}/run", response_model=IngestionRunOut, status_code=status.HTTP_201_CREATED)
def run_source(
    candidate_id: str,
    source_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IngestionRun:
    candidate = require_candidate(candidate_id, user, db)
    source = require_source(candidate_id, source_id, user, db)
    if not source.is_enabled:
        raise HTTPException(status.HTTP_409_CONFLICT, "Enable this source before running it")
    source.last_run_at = utc_now()
    db.commit()
    try:
        return execute_connector(db, user, candidate, source.provider, source.source_key)
    except ConnectorExecutionFailed as error:
        raise HTTPException(
            error.status_code,
            f"{error.run.error_message}. Ingestion run: {error.run.id}",
        ) from error


@router.get("/jobs", response_model=CandidateJobPage)
def list_candidate_jobs(
    candidate_id: str,
    decision: str | None = None,
    provider: str | None = None,
    q: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateJobPage:
    candidate = require_candidate(candidate_id, user, db)
    statement = select(Job).where(Job.owner_id == user.id, Job.candidate_id == candidate.id)
    if decision is not None:
        statement = statement.where(Job.decision == decision)
    if provider is not None:
        source_job_ids = select(JobSourceRecord.job_id).where(
            JobSourceRecord.owner_id == user.id,
            JobSourceRecord.candidate_id == candidate.id,
            JobSourceRecord.provider == provider,
        )
        statement = statement.where(Job.id.in_(source_job_ids))
    if q:
        pattern = f"%{q.strip()}%"
        statement = statement.where(
            or_(Job.company.ilike(pattern), Job.title.ilike(pattern), Job.description.ilike(pattern))
        )
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = list(db.execute(statement.order_by(Job.created_at.desc()).offset(offset).limit(limit)).scalars())
    return CandidateJobPage(
        items=[CandidateJobOut.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/jobs/manual", response_model=ManualJobIntakeOut, status_code=status.HTTP_201_CREATED)
def create_manual_job(
    candidate_id: str,
    payload: ManualJobCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ManualJobIntakeOut:
    candidate = require_candidate(candidate_id, user, db)
    provider, canonical_url = canonicalize_manual_job_url(payload.url)
    external_id = hashlib.sha256(canonical_url.encode()).hexdigest()
    run = ingest_records(
        db,
        user,
        candidate,
        provider,
        "manual-link",
        [
            ExternalJob(
                external_id=external_id,
                company=payload.company,
                title=payload.title,
                location=payload.location,
                url=canonical_url,
                source=provider,
                description=payload.description,
                raw_payload={"intake": "user_confirmed"},
            )
        ],
    )
    source_record = db.execute(
        select(JobSourceRecord).where(
            JobSourceRecord.candidate_id == candidate.id,
            JobSourceRecord.provider == provider,
            JobSourceRecord.source_key == "manual-link",
            JobSourceRecord.external_id == external_id,
        )
    ).scalar_one()
    job = require_job(candidate.id, source_record.job_id, user, db)
    record_event(
        db,
        owner_id=user.id,
        candidate_id=candidate.id,
        action="job.manually_added",
        entity_type="job",
        entity_id=str(job.id),
        metadata={"provider": provider, "created": run.created_count == 1},
    )
    db.commit()
    db.refresh(job)
    return ManualJobIntakeOut(job=CandidateJobOut.model_validate(job), created=run.created_count == 1)


def require_job(candidate_id: str, job_id: int, user: User, db: Session) -> Job:
    job = db.execute(
        select(Job).where(Job.id == job_id, Job.candidate_id == candidate_id, Job.owner_id == user.id)
    ).scalar_one_or_none()
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job


@router.patch("/jobs/{job_id}/decision", response_model=CandidateJobOut)
def review_candidate_job(
    candidate_id: str,
    job_id: int,
    payload: CandidateDecisionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    require_candidate(candidate_id, user, db)
    job = require_job(candidate_id, job_id, user, db)
    job.decision = payload.decision
    job.status = {
        "approve": "approved_for_application",
        "maybe": "needs_review",
        "skip": "closed_skipped",
        "new": "discovered",
    }[payload.decision]
    record_event(
        db,
        owner_id=user.id,
        candidate_id=candidate_id,
        action="job.reviewed",
        entity_type="job",
        entity_id=str(job.id),
        metadata={"decision": payload.decision},
    )
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs/{job_id}/provenance", response_model=list[JobProvenanceOut])
def job_provenance(
    candidate_id: str,
    job_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[JobSourceRecord]:
    require_candidate(candidate_id, user, db)
    job = require_job(candidate_id, job_id, user, db)
    return list(
        db.execute(
            select(JobSourceRecord)
            .where(JobSourceRecord.owner_id == user.id, JobSourceRecord.job_id == job.id)
            .order_by(JobSourceRecord.first_seen_at)
        ).scalars()
    )
