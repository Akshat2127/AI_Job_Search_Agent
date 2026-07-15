import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.db.session import SessionLocal
from backend.app.models.job import Job  # noqa
from backend.app.schemas.job import JobCreate
from backend.app.services.jobs import create_job


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    df = pd.read_csv(args.csv).fillna("")
    db = SessionLocal()
    count = 0
    try:
        for _, row in df.iterrows():
            payload = JobCreate(
                company=row.get("company", ""),
                title=row.get("title", ""),
                location=row.get("location", ""),
                remote_type=row.get("remote_type", ""),
                url=row.get("url", ""),
                source=row.get("source", "csv"),
                description=row.get("description", ""),
            )
            create_job(db, payload)
            count += 1
    finally:
        db.close()
    print(f"Imported/processed {count} jobs")


if __name__ == "__main__":
    main()
