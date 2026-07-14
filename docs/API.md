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
