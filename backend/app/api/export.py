import csv, io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.services.jobs import list_jobs

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/jobs.csv")
def export_jobs(db: Session = Depends(get_db)):
    rows = list_jobs(db)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["id","company","title","location","remote_type","fit_score","decision","status","url","score_reason","resume_variant"])
    for j in rows:
        writer.writerow([j.id,j.company,j.title,j.location,j.remote_type,j.fit_score,j.decision,j.status,j.url,j.score_reason,j.resume_variant])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=jobs.csv"})
