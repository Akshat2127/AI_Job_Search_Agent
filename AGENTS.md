# JobAgent AI Repository Instructions

## Purpose

Build a privacy-conscious, human-controlled job-search platform that helps users discover, assess, prepare for, and track applications. Application quality and grounded candidate facts take priority over volume. The system must never submit an application, send a message, or create a calendar event without the required explicit user approval.

## Architecture

Use a modular monolith. FastAPI and SQLAlchemy live under `backend/app`; the React/TypeScript client lives under `frontend`; safe browser assistance lives under `browser`; migrations live under `backend/alembic`; automated tests live under `tests`. PostgreSQL is the production database and SQLite is a local/test convenience. Keep integrations behind interfaces and configurable boundaries. Preserve backward compatibility while `/api/v1` replaces legacy routes.

Read `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and `docs/PROGRESS.md` before a substantial change. Add an architecture decision before a major or hard-to-reverse change, including a migration and rollback path.

## Supported Commands

- `make setup`: create the Python environment and install dependencies.
- `make run`: run the local API.
- `make import`, `make score`, `make export`: exercise the legacy sample workflow.
- `make test`: run backend tests.
- `docker compose config`: validate Compose; `docker compose up --build` starts the container stack.

Keep these commands accurate as tooling evolves. Prefer adding focused `make` targets rather than undocumented command sequences.

## Coding Standards

- Python: Pydantic v2, SQLAlchemy 2 typed mappings, Ruff formatting/linting, useful type annotations, UTC-aware timestamps, and small service/repository boundaries.
- TypeScript: strict mode, accessible semantic components, validated forms, explicit loading/error/empty states, ESLint and formatting.
- APIs: version new endpoints under `/api/v1`; validate all input; use consistent safe errors, pagination, ownership checks, and idempotency where operations may repeat.
- Integrations: use explicit timeouts, bounded retries/backoff, rate limits, structured errors, provenance, and deterministic test fakes. Unit tests must never make live network or AI calls.
- Do not leave placeholders presented as working features. Label incomplete or credential-gated behavior accurately.

## Testing Requirements

Every behavior change needs proportionate deterministic tests. Cover success, validation, authorization, failure, and deduplication paths where relevant. Run backend tests, lint, formatting checks, type checks, frontend tests/type checks/lint/build, migration checks, and relevant end-to-end tests before declaring a milestone complete. Never fake, omit, or misreport test results; report commands and failures exactly.

## Security and Privacy

- Never commit secrets, `.env`, OAuth tokens, personal resumes, personal databases, generated caches, or unredacted sensitive logs.
- Treat resumes, application answers, email, access tokens, and candidate data as sensitive. Minimize retention and redact logs/audits.
- Validate upload type, signature, size, and path; prevent traversal. Validate outbound URLs and block SSRF targets. Sanitize untrusted HTML.
- Enforce user and candidate ownership in every data access path. Production must fail closed when secure auth, encryption, or secrets are missing.
- Never bypass CAPTCHA, rate limits, robots rules, authentication, or access controls. Do not automate LinkedIn or Indeed contrary to their terms.
- Do not infer work authorization, sponsorship, demographic, salary, or other sensitive/legal answers.
- Never click final application submit, send email, or modify calendars automatically. Require explicit, scoped approval and audit it.

## Git Workflow

Work on a feature branch. Preserve unrelated user changes. Make small conventional commits only after checks pass. Do not rewrite history, push, tag, or change repository settings without authorization. Do not commit a milestone with failing required checks. Keep the repository runnable after each commit.

## Definition of Done

A feature is done only when implementation, migration (if needed), tests, errors, security/privacy review, UI states, and user/developer documentation are complete and relevant checks pass. A milestone additionally requires a clean Git status and a conventional local commit. Update documentation whenever behavior, configuration, limitations, operations, or architecture changes. Never claim an integration or test is working unless it actually ran; credential-gated integrations must include full configuration, safe errors, tests using fakes, and an explicit disabled state.

