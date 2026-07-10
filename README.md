# JobAgent AI

A human-approved AI job search automation platform.

## Quick start

```bash
cd jobagent-ai-full
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
python scripts/import_jobs.py --csv data/sample_jobs.csv
uvicorn backend.app.main:app --reload --port 8000
```

Open:

```text
http://localhost:8000/docs
```

## Useful commands

```bash
python scripts/import_jobs.py --csv data/sample_jobs.csv
python scripts/run_scoring.py
python scripts/export_google_sheets.py --out output/google_sheets
pytest
```

## Docker

```bash
docker compose up --build
```

## Architecture
See `docs/PLAN.md` and `docs/ARCHITECTURE.md`.


## Dashboard

After starting the backend, open:

```
http://localhost:8000/
```

The dashboard lets you filter jobs, inspect fit reasons, preview recruiter messages and cover letters, and mark each job as approve/maybe/skip.

```bash
uvicorn backend.app.main:app --reload --port 8000
```
