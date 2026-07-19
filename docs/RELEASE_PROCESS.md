# Release process

`main` is the releasable branch. Development happens on short-lived `feature/*`
branches and reaches `main` only through a reviewed pull request whose required CI
checks pass. Do not deploy a feature branch as production.

## Local pre-production

The pre-production Compose override uses a separate project name, ports, database,
upload volume, and cookie names, so validation cannot alter the normal local stack:

```bash
make preprod-up
```

Open `http://localhost:3100`; API readiness is at
`http://localhost:8100/api/v1/readiness`. Stop the environment without deleting its
volumes using `make preprod-down`. The checked-in password is intentionally limited
to this local simulation and must never be used for a hosted environment.

## Promotion

1. Run `make check` on the feature branch and complete focused live validation.
2. Push the feature branch and open a pull request into `main`.
3. Require the GitHub `checks` job and at least one review before merge.
4. Deploy the exact merge commit to an isolated hosted staging environment.
5. Run health, migration, authentication, ownership, ingestion, and persistence
   smoke tests with synthetic data. External writes remain disabled.
6. Create an annotated semantic tag such as `v0.1.0` on the validated merge commit.
7. Build production images from that tag—not from a mutable branch—and record image
   digests. Production promotion requires an explicit human approval.

## Hosted environment boundaries

Staging and production require separate PostgreSQL databases, upload storage,
domains, encryption/secrets, OAuth applications, and external-provider credentials.
Production uses `APP_ENV=production`, `AUTH_MODE=password`, JSON logs, HTTPS, and
secure cookies. Never copy candidate or resume data from production into staging.

Before a production migration, take and verify a database backup. Keep the previous
versioned images available. Roll back application images first when the migration is
backward compatible; destructive schema rollback requires its documented migration
procedure and explicit approval.

Repository branch protection and hosted deployment environments are GitHub/account
settings and are not claimed as active until configured and verified remotely.
