from sqlalchemy.orm import Session

from backend.app.schemas.job import JobCreate
from backend.app.services.ats_connectors import GreenhouseConnector, LeverConnector
from backend.app.services.jobs import create_job


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
