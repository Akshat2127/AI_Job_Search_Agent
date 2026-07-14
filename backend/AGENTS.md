# Backend Instructions

Follow the root `AGENTS.md`. Keep HTTP handlers thin: schemas validate transport data, services own workflows, repositories own persistence, and integrations isolate external systems. New public APIs belong under `/api/v1`; retain tested legacy compatibility during migration.

Do not call `Base.metadata.create_all` during application import in production. Schema evolution must use Alembic. Use injected sessions and clients, parameterized ORM queries, UTC-aware timestamps, bounded network operations, and redacted structured logging. Every record containing candidate data must have an enforceable ownership path. External URL fetching requires SSRF protection.

Backend changes require focused unit/service/API tests and, when models change, a migration and migration test. Tests must use isolated temporary databases and fake external providers.

