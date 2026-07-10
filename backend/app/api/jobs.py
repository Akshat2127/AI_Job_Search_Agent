from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.job import Job
from backend.app.schemas.job import JobCreate, JobOut, DecisionUpdate
from backend.app.services.jobs import create_job, list_jobs, enrich_job

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("", response_model=list[JobOut])
def get_jobs(min_score: int | None = None, decision: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    return list_jobs(db, min_score=min_score, decision=decision, q=q)

@router.post("", response_model=JobOut)
def post_job(payload: JobCreate, db: Session = Depends(get_db)):
    return create_job(db, payload)

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job

@router.patch("/{job_id}/decision", response_model=JobOut)
def update_decision(job_id: int, payload: DecisionUpdate, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job.decision = payload.decision
    if payload.decision == "approve":
        job.status = "approved_for_application"
    elif payload.decision == "skip":
        job.status = "closed_skipped"
    elif payload.decision == "maybe":
        job.status = "needs_review"
    db.commit()
    db.refresh(job)
    return job

@router.post("/{job_id}/score", response_model=JobOut)
def rescore(job_id: int, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    enrich_job(job)
    db.commit()
    db.refresh(job)
    return job
