import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.db.session import SessionLocal
from backend.app.services.jobs import list_jobs

parser = argparse.ArgumentParser()
parser.add_argument("--out", default="output/google_sheets")
args = parser.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
db = SessionLocal()
try:
    jobs = list_jobs(db)
    rows = [
        {
            "id": j.id,
            "company": j.company,
            "title": j.title,
            "location": j.location,
            "fit_score": j.fit_score,
            "decision": j.decision,
            "status": j.status,
            "url": j.url,
            "score_reason": j.score_reason,
            "resume_variant": j.resume_variant,
        }
        for j in jobs
    ]
    df = pd.DataFrame(rows)
    df.to_csv(out / "tracker.csv", index=False)
    if not df.empty:
        df[df.decision.eq("new")].to_csv(out / "review.csv", index=False)
        df[df.decision.eq("approve")].to_csv(out / "approved.csv", index=False)
        df[df.decision.eq("maybe")].to_csv(out / "maybe.csv", index=False)
        df[df.decision.eq("skip")].to_csv(out / "skipped.csv", index=False)
    print(f"Exported to {out}")
finally:
    db.close()
