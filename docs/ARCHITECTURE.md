# Architecture

- FastAPI exposes REST endpoints.
- SQLAlchemy stores jobs and generated artifacts.
- Services contain scoring, draft generation, analytics, and ingestion logic.
- Workers are designed to run scheduled ingestion later with Celery/Redis.
- Frontend is scaffolded for a dashboard that calls the API.
- Playwright assistant is scaffolded for safe, manual-submit application help.
