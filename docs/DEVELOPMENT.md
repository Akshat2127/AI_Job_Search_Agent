# Development

## Prerequisites

- Python 3.12 or 3.13 for local development.
- Node.js 22.
- Docker with Compose for the production-like stack.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cp .env.example .env
.venv/bin/alembic upgrade head
npm --prefix frontend ci
```

For Homebrew's keg-only Node installation, first run `export PATH="$(brew --prefix node@22)/bin:$PATH"`.

Run the API and frontend in separate terminals:

```bash
.venv/bin/uvicorn backend.app.main:app --reload --port 8000
npm --prefix frontend run dev
```

## Verification

`make check` is the authoritative current local gate. It runs backend tests, migration coverage, Ruff lint/format checks, mypy, an ASGI runtime smoke test, frontend lint/types/tests/build, Compose validation, and whitespace checks.

The smoke test creates a temporary database, migrates it from zero to Alembic head, and verifies `/api/v1/health`, `/api/v1/readiness`, and `/api/v1/jobs`. It never reads or changes the developer's `jobagent.db`. To inspect a running process manually:

```bash
curl -fsS http://localhost:8000/api/v1/health
curl -fsS http://localhost:8000/api/v1/readiness
curl -fsS http://localhost:8000/api/v1/jobs
```

## Database migrations

Fresh databases use `.venv/bin/alembic upgrade head`. Application startup does not create production tables.

The original local `jobagent.db` already has the schema represented by revision `20260713_0001`. Preserve it before stamping:

```bash
cp jobagent.db jobagent.db.backup
.venv/bin/alembic stamp 20260713_0001
.venv/bin/alembic current
```

Do not run `stamp` on an empty database; use `upgrade head`. Never commit either database or backup. A destructive downgrade requires explicit approval and a verified backup.

## Docker

```bash
docker compose up --build
docker compose ps
```

The API waits for PostgreSQL health, applies migrations, and then starts as a non-root user. The frontend waits for API readiness. PostgreSQL data uses the `pgdata` volume and resume files use the `uploads` volume, so both survive container recreation. Development credentials in Compose are local-only and must not be reused in production.

For an isolated local pre-production rehearsal, use `make preprod-up` and open
`http://localhost:3100`. It has distinct containers, ports, cookies, PostgreSQL data,
and uploads. See `docs/RELEASE_PROCESS.md` for promotion and rollback requirements.
