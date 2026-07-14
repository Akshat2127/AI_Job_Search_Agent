# Architecture Decisions

## ADR-001: Incremental modular-monolith migration

Status: accepted, 2026-07-13.

The existing application has useful job import, scoring, decisions, drafts, export, and a static dashboard, but one global database/session and a single legacy job model. Replacing it in one operation risks losing the working sample workflow and local data.

We will introduce modules and `/api/v1` incrementally, keep tested legacy routes temporarily, and use one PostgreSQL database with Alembic migrations. We will not introduce microservices without measured scaling or isolation requirements.

Migration path:

1. Establish typed settings, lifecycle-managed database startup, Alembic, logging, errors, quality checks, and compatibility tests.
2. Add users/candidates and ownership, then migrate existing jobs to an explicit local owner/candidate through a data migration.
3. Normalize provenance, ingestion, matching, artifacts, and applications in additive migrations.
4. Move the frontend to `/api/v1`, warn on legacy routes, then remove them only in a documented major release.

Rollback uses database backups plus Alembic downgrade where verified. Additive columns/tables are preferred; destructive migrations require an export/backup and explicit approval. The tracked legacy SQLite file is not a migration artifact and must not contain personal data in version control.

## ADR-002: PostgreSQL production, SQLite local/test

Status: accepted, 2026-07-13.

PostgreSQL supplies production concurrency, constraints, indexing, JSON, and migration behavior. SQLite keeps onboarding and isolated tests lightweight. Code and migrations must be tested for both where SQL differs; production configuration must reject SQLite.

## ADR-003: Human-controlled external actions

Status: accepted, 2026-07-13.

Submission, email sending, and calendar writes require an explicit scoped confirmation immediately before the action. Dry-run and draft creation are separate audited operations. CAPTCHA and access controls always pause automation.

