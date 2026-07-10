# JobAgent AI - Production Plan

## Goal
Build a human-approved AI job search platform that automates discovery, dedupe, fit scoring, drafting, tracking, exports, and application preparation while keeping the final submission under user control.

## Core principles
1. Human approval before applying.
2. Avoid prohibited bot behavior on LinkedIn/Indeed; use alert emails and official/company ATS pages where possible.
3. Store every decision and generated artifact for auditability.
4. Make integrations replaceable: SQLite locally, PostgreSQL in Docker/cloud; mock LLM locally, OpenAI/Claude later.
5. Keep data portable through CSV exports and Google Sheets-compatible files.

## Features in this package
- FastAPI backend with OpenAPI docs
- SQLAlchemy database layer, SQLite default, PostgreSQL-ready
- Job CRUD, scoring, decision workflow, analytics, export
- Candidate profile and scoring engine
- Draft generator for cover letters/recruiter messages
- ATS connector skeletons: Greenhouse, Lever, generic career page
- Gmail alert parser skeleton
- Background worker command skeleton
- Next.js-style frontend scaffold with dashboard design
- Playwright application-assistant skeleton with manual-submit gate
- Docker Compose for API + Postgres + Redis
- Tests and sample data
- Makefile commands

## Production roadmap after this package
1. Google OAuth + Gmail API + Sheets API
2. Real LLM provider integration and prompt versioning
3. Alembic migrations
4. Celery/Redis scheduled ingestion
5. Full React dashboard
6. Browser autofill plugins per ATS
7. Deployment to Fly.io/Render/AWS/GCP
