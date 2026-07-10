import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.db.session import SessionLocal
from backend.app.models.job import Job
from backend.app.services.jobs import enrich_job

db = SessionLocal()
try:
    for job in db.query(Job).all():
        enrich_job(job)
    db.commit()
    print("Rescored jobs")
finally:
    db.close()
