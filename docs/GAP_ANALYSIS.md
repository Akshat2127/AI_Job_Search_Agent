# Baseline Gap Analysis

Audit date: 2026-07-13. Baseline commit: `2b533f3`.

## Working and verified

- FastAPI starts and exposes health, job list/create/detail/decision/rescore, analytics, and CSV export.
- SQLite job persistence, sample CSV import, rule scoring, deterministic draft text, and static dashboard exist.
- Lever and Greenhouse clients perform simple public endpoint requests.
- Three baseline tests pass; sample import, rescoring, and export run locally.

## Misleading, incomplete, or unsafe

- React package metadata names Next.js but has no valid Next/Vite application or TypeScript/test/lint setup.
- ATS clients lack injected HTTP clients, retry/backoff, rate limits, pagination/run audit, raw payloads, and mocked tests.
- Gmail, worker scheduling, Playwright, and n8n content are placeholders, not integrations.
- Drafts hard-code candidate claims and identity with no fact/evidence records or approval state.
- Job URL input/fetching has no SSRF validation; HTML descriptions are not sanitized at ingestion.
- No authentication, ownership, candidate records, authorization isolation, CSRF strategy, audit log, or privacy controls.
- No Alembic; tables are created during module import. PostgreSQL is configured but unverified.
- No normalized provenance, dedupe aliases, stable UUIDs, pagination, standard errors, structured logging, readiness, or request IDs.
- Pydantic class configuration is deprecated and timestamps are naive UTC.
- The repository tracks bytecode, a local SQLite database, and generated exports despite ignore rules.
- Docker lacks production hardening/health checks; Redis has no working consumer; CI and quality tooling are absent.

## Risk order

1. Privacy/secret leakage and cross-user access.
2. Ungrounded generated claims and unsafe outbound URL handling.
3. Data loss from schema changes without migrations/backups.
4. External-service failures or terms violations from simplistic connectors/automation.
5. False confidence from a broken frontend and missing end-to-end coverage.

This document is an audit, not a claim that later milestones are implemented.

