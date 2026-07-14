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

The current FastAPI-served dashboard is available at `http://localhost:8000/`.

## Frontend development

The evolving React/TypeScript client requires Node.js 22. On Homebrew installations, `node@22` is keg-only; add it to the current shell before using npm:

```bash
export PATH="$(brew --prefix node@22)/bin:$PATH"
npm --prefix frontend install
npm --prefix frontend run dev
```

Open `http://localhost:3000`. Keep the API running on port 8000; Vite proxies the current jobs and analytics endpoints during development.

The React client is a tested recovery baseline with summary and job-list loading/error/empty states. It is not yet the complete review dashboard described in the roadmap.

## Useful commands

```bash
python scripts/import_jobs.py --csv data/sample_jobs.csv
python scripts/run_scoring.py
python scripts/export_google_sheets.py --out output/google_sheets
pytest
```

Run the complete currently configured check suite:

```bash
export PATH="$(brew --prefix node@22)/bin:$PATH"
make check
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
