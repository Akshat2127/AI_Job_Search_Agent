from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_versioned_health_and_readiness_include_request_id():
    health = client.get("/api/v1/health", headers={"X-Request-ID": "test-request"})
    readiness = client.get("/api/v1/readiness")

    assert health.status_code == 200
    assert health.headers["X-Request-ID"] == "test-request"
    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ready", "database": "available"}


def test_versioned_jobs_route_preserves_legacy_compatibility():
    legacy = client.get("/jobs")
    versioned = client.get("/api/v1/jobs")

    assert legacy.status_code == 200
    assert versioned.status_code == 200
    assert versioned.json() == legacy.json()


def test_job_rejects_active_content_url():
    response = client.post(
        "/jobs",
        json={"company": "Example", "title": "Business Analyst", "url": "javascript:alert(1)"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_missing_job_uses_safe_error_schema():
    response = client.get("/api/v1/jobs/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
    assert response.json()["error"]["message"] == "Job not found"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_job_rejects_embedded_url_credentials():
    response = client.post(
        "/jobs",
        json={"company": "Example", "title": "Business Analyst", "url": "https://user:pass@example.com/job"},
    )

    assert response.status_code == 422


def test_job_rejects_reversed_salary_range():
    response = client.post(
        "/jobs",
        json={
            "company": "Example",
            "title": "Business Analyst",
            "url": "https://example.com/job",
            "salary_min": 120000,
            "salary_max": 100000,
        },
    )

    assert response.status_code == 422
