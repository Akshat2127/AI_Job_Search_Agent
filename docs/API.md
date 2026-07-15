# API

New APIs are versioned under `/api/v1`. Legacy unversioned jobs, analytics, and export routes remain temporarily available for the original static dashboard.

## System endpoints

- `GET /api/v1/health`: process liveness and application version.
- `GET /api/v1/readiness`: database connectivity; returns HTTP 503 when unavailable.

## Current job endpoints

- `GET /api/v1/jobs`: list jobs using the existing optional `min_score`, `decision`, and `q` filters.
- `POST /api/v1/jobs`: create, score, and deduplicate a job.
- `GET /api/v1/jobs/{id}`: retrieve a job.
- `PATCH /api/v1/jobs/{id}/decision`: update the review decision.
- `POST /api/v1/jobs/{id}/score`: rerun deterministic scoring.
- `GET /api/v1/analytics/summary`: legacy aggregate summary.
- `GET /api/v1/export/jobs.csv`: export current jobs.

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

## Milestone 2 preview APIs

The in-progress candidate backend exposes:

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, and `POST /api/v1/auth/logout`.
- `GET|POST /api/v1/candidates` and `GET|PATCH /api/v1/candidates/{id}`.
- Candidate-owned preferences, skills, experiences, application answers, and resume endpoints below `/api/v1/candidates/{id}`.
- Candidate-owned projects, education, and certifications use the same nested route structure.
- `GET /api/v1/audit` returns only the authenticated owner's activity, optionally filtered by candidate.

Password login returns an opaque bearer token; only its SHA-256 digest is stored. Development mode may create one configured local identity, but only for localhost/test clients. Production startup rejects development authentication. Browser cookie/CSRF delivery and the frontend sign-in flow are still pending, so this API must not yet be exposed publicly.

Resume upload accepts PDF and DOCX up to `MAX_RESUME_BYTES`, validates the declared type, extension, and file signature, extracts text, stores the file below the gitignored `UPLOAD_ROOT`, and marks it `needs_review`. Extracted text is not a confirmed candidate fact until the user approves it.

Uploading the same file twice for one candidate returns HTTP 409. Deleting a resume removes both its database record and owned local file after path-boundary validation. Resume metadata includes version/master/archive fields; full version promotion remains in progress.
