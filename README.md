# JobAgent AI

A human-approved AI job search automation platform.

## Quick start

The fastest usable local version runs the complete stack with Docker:

```bash
docker compose up --build --detach
```

Open `http://localhost:3000`, choose **Create account**, and then:

1. Create a candidate profile.
2. Open **Discovery**, save a Greenhouse or Lever source key, and run it.
3. Search the candidate-owned jobs and mark each one approve, maybe, or skip.

This is a local basic alpha: discovery and human review work, but scheduled refresh,
matching, document generation, and application submission are not implemented yet.

For backend-only development:

```bash
cd jobagent-ai-full
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
alembic upgrade head
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

The React client now provides the basic account, candidate knowledge-base, source
discovery, and candidate-owned job-review journey. It is not yet the complete
production dashboard described in the roadmap.

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

Compose starts PostgreSQL, runs Alembic migrations before the API, and serves the React frontend at `http://localhost:3000`. API readiness is available at `http://localhost:8000/api/v1/readiness`.

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
