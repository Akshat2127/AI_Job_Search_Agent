# API

New APIs are versioned under `/api/v1`. Legacy unversioned jobs, analytics, and export routes remain temporarily available for the original static dashboard.

## System endpoints

- `GET /api/v1/health`: process liveness and application version.
- `GET /api/v1/readiness`: database connectivity; returns HTTP 503 when unavailable.

## Temporary legacy job endpoints

- `GET /api/v1/jobs`: list jobs using the existing optional `min_score`, `decision`, and `q` filters.
- `POST /api/v1/jobs`: create, score, and deduplicate a job.
- `GET /api/v1/jobs/{id}`: retrieve a job.
- `PATCH /api/v1/jobs/{id}/decision`: update the review decision.
- `POST /api/v1/jobs/{id}/score`: rerun deterministic scoring.
- `GET /api/v1/analytics/summary`: legacy aggregate summary.
- `GET /api/v1/export/jobs.csv`: export current jobs.

These compatibility routes only access legacy jobs whose `candidate_id` is null. Candidate-owned ingested jobs never appear through these unauthenticated routes.

Every HTTP response includes `X-Request-ID`. A caller-supplied `X-Request-ID` is preserved. Validation errors use:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [],
    "request_id": null
  }
}
```

Authentication, ownership, pagination envelopes, and normalized domain APIs arrive in subsequent milestones. The current endpoints must not be exposed publicly.

## Candidate knowledge APIs

The in-progress candidate backend exposes:

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, and `POST /api/v1/auth/logout`.
- `GET|POST /api/v1/candidates` and `GET|PATCH /api/v1/candidates/{id}`.
- Candidate-owned preferences, skills, experiences, application answers, and resume endpoints below `/api/v1/candidates/{id}`.
- Candidate-owned projects, education, and certifications use the same nested route structure.
- `GET /api/v1/audit` returns only the authenticated owner's activity, optionally filtered by candidate.

Password login returns an opaque bearer token for non-browser clients; only its SHA-256 digest is stored. `POST /api/v1/auth/browser-login` instead delivers that token in a SameSite=Strict HttpOnly cookie and sets a readable CSRF cookie. Cookie-authenticated POST/PATCH/PUT/DELETE requests must echo the CSRF value in `X-CSRF-Token`. Logout revokes only the active session and clears both cookies. Production startup rejects development authentication and non-secure session cookies.

Development mode may create one configured local identity, but only for localhost/test clients. The React client checks `/auth/me`, displays sign-in/sign-out controls when appropriate, includes credentials, and attaches CSRF headers to mutations. TLS termination remains mandatory in production.

Resume upload accepts PDF and DOCX up to `MAX_RESUME_BYTES`, validates the declared type, extension, and file signature, extracts text, stores the file below the gitignored `UPLOAD_ROOT`, assigns a sequential candidate-local version number, and marks it `needs_review`. Extracted text is not a confirmed candidate fact until the user approves it.

Uploading the same file twice for one candidate returns HTTP 409. Deleting a resume removes both its database record and owned local file after path-boundary validation. Resume metadata includes a user-editable label plus version, master, and archive fields.

`PATCH /api/v1/candidates/{candidate_id}/resumes/{resume_id}` reviews extracted text and can promote one approved resume as master. Promoting a master demotes the previous master. Master extracted text is immutable; upload a new resume version rather than silently changing confirmed source material.

The candidate workspace exposes preference, skill, employment, project, education, certification, sensitive application-answer, resume review/master, and owner-scoped audit workflows. Sensitive answers remain visibly marked for per-application confirmation and are never inferred.

## Ingestion checkpoint APIs

- `POST /api/v1/candidates/{candidate_id}/ingestion-runs` accepts an authenticated bounded fixture batch for deterministic connector development.
- `POST /api/v1/candidates/{candidate_id}/connector-runs` executes an authenticated public `greenhouse` or `lever` source.
- `GET /api/v1/candidates/{candidate_id}/ingestion-runs` lists only that owner and candidate's runs.
- `GET|POST /api/v1/candidates/{candidate_id}/sources` lists or creates saved connector sources.
- `PATCH /api/v1/candidates/{candidate_id}/sources/{source_id}` changes the label or enabled state.
- `POST /api/v1/candidates/{candidate_id}/sources/{source_id}/run` executes an enabled saved source.

Each record requires a provider external ID and public HTTP(S) job URL. The service stores source provenance, converts description HTML to plain text, bounds raw payloads to 256 KB, canonicalizes tracking parameters, retains source aliases, and deduplicates within the candidate. Completion is audited without copying raw payloads into the audit log.

Connector source keys are strict slugs and requests use fixed provider HTTPS hosts, so callers cannot supply an arbitrary fetch URL. Requests have connect/read timeouts, bounded retry/backoff for timeouts, HTTP 429, and transient 5xx responses, request pacing, and provider-specific result limits. Lever uses its documented `skip`/`limit` pagination; Greenhouse's public job-board list returns the board's published jobs in one response. Failed executions persist a safe error code/message and owner-scoped audit event. The connector API only reads public postings and never submits applications.

## Candidate job review APIs

- `POST /api/v1/candidates/{candidate_id}/jobs/manual` accepts user-confirmed job
  details for a LinkedIn or Indeed job URL. It canonicalizes the URL, removes known
  tracking parameters, preserves provider job identifiers, records provenance, and
  returns `created: false` when the same candidate already owns the job.
- `GET /api/v1/candidates/{candidate_id}/jobs` returns an owner-scoped page with `items`, `total`, `limit`, and `offset`; optional `q`, `provider`, and `decision` filters are supported.
- `PATCH /api/v1/candidates/{candidate_id}/jobs/{job_id}/decision` accepts `new`, `approve`, `maybe`, or `skip` and audits the decision.
- `GET /api/v1/candidates/{candidate_id}/jobs/{job_id}/provenance` returns retained source aliases and first/last-seen timestamps without exposing stored raw payloads.

Cross-owner source and job identifiers return HTTP 404. Saved disabled sources return HTTP 409 when execution is attempted. The React workspace provides saved-source controls, paginated job review, official posting links, and provenance inspection.

Manual intake never fetches or scrapes LinkedIn or Indeed. The user supplies and
confirms the company, title, location, and optional description. General search API
integration remains disabled until approved provider access and credentials exist.
