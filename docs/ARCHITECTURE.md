# Architecture

## Decision summary

JobAgent AI is a modular monolith. This keeps transactions, authorization, deployment, and local development understandable while the product domain is still evolving. Modules communicate through explicit Python interfaces rather than separate network services.

```text
React/TypeScript client
        |
FastAPI /api/v1 + temporary legacy routes
        |
application services --- integration interfaces (ATS, email, AI, storage, calendar)
        |
repositories / SQLAlchemy 2
        |
PostgreSQL production | SQLite local/test

scheduler/worker -> the same application services
browser assistant -> explicit per-session approval gate
```

## Boundaries

- `api`: HTTP validation, authentication context, status mapping.
- `schemas`: transport and structured-output contracts.
- `services`: use cases, authorization-aware orchestration, transactions.
- `repositories`: queries, persistence, pagination, ownership filters.
- `models` and `db`: normalized persistence and Alembic migrations.
- `integrations`: replaceable external clients with timeouts, retries, rate controls, provenance, and fakes.
- `security` and `observability`: cross-cutting authorization, URL/upload safety, redaction, request IDs, and audit events.
- `workers`: idempotent scheduled/manual jobs calling application services.

## Data and trust

Candidate-confirmed facts are the grounding source. Extracted/inferred resume data remains unconfirmed until reviewed. Deterministic eligibility is computed before optional AI fit analysis. Generated artifacts record inputs, evidence references, provider/model, prompt version, timestamps, user edits, and approval state.

## Deployment

The first production-like target is Docker Compose with separate API, frontend, worker (when introduced), and PostgreSQL containers. Containers use health checks and persistent storage; a reverse proxy terminates TLS. SQLite remains a local/test option only. See `docs/DECISIONS.md` for migration constraints.
