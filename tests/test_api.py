from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'


def test_job_rejects_active_content_url():
    response = client.post(
        "/jobs",
        json={"company": "Example", "title": "Business Analyst", "url": "javascript:alert(1)"},
    )

    assert response.status_code == 422


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
