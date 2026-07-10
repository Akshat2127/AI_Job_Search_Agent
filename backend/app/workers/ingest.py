from sqlalchemy.orm import Session
from backend.app.services.ats_connectors import LeverConnector, GreenhouseConnector
from backend.app.services.jobs import create_job
from backend.app.schemas.job import JobCreate

def ingest_lever(db: Session, company_slug: str) -> int:
    count = 0
    for ext in LeverConnector().fetch(company_slug):
        create_job(db, JobCreate(**ext.__dict__))
        count += 1
    return count

def ingest_greenhouse(db: Session, board_token: str) -> int:
    count = 0
    for ext in GreenhouseConnector().fetch(board_token):
        create_job(db, JobCreate(**ext.__dict__))
        count += 1
    return count
