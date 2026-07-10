from collections import Counter
from sqlalchemy.orm import Session
from backend.app.services.jobs import list_jobs

def summary(db: Session) -> dict:
    jobs = list_jobs(db)
    by_decision = Counter(j.decision for j in jobs)
    excellent = [j for j in jobs if j.fit_score >= 80]
    approved = [j for j in jobs if j.decision == "approve"]
    return {
        "total_jobs": len(jobs),
        "excellent_matches": len(excellent),
        "approved": len(approved),
        "by_decision": dict(by_decision),
        "top_companies": Counter(j.company for j in jobs).most_common(10),
        "average_score": round(sum(j.fit_score for j in jobs) / len(jobs), 1) if jobs else 0,
    }
