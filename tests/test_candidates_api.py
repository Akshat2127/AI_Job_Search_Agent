import io

from docx import Document
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.ats_connectors import ConnectorError, ExternalJob

client = TestClient(app)


def create_account(email: str) -> str:
    registration = client.post(
        "/api/v1/auth/register", json={"email": email, "password": "correct horse battery staple"}
    )
    assert registration.status_code == 201, registration.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "correct horse battery staple"})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_candidate_profile_preferences_and_sensitive_answers():
    token = create_account("profile-owner@example.com")
    headers = authorization(token)
    created = client.post(
        "/api/v1/candidates",
        headers=headers,
        json={"display_name": "Gurbani Sharma", "headline": "Senior Business Systems Analyst", "years_experience": 12},
    )
    assert created.status_code == 201, created.text
    candidate_id = created.json()["id"]

    preference = client.put(
        f"/api/v1/candidates/{candidate_id}/preferences",
        headers=headers,
        json={
            "target_roles": ["Senior Business Analyst", "Senior Business Analyst"],
            "preferred_locations": ["Bothell, WA", "Remote US"],
            "remote_preferences": ["remote", "hybrid"],
            "work_authorization": None,
            "sponsorship_required": None,
        },
    )
    assert preference.status_code == 200
    assert preference.json()["target_roles"] == ["Senior Business Analyst"]
    assert preference.json()["sponsorship_required"] is None

    answer = client.put(
        f"/api/v1/candidates/{candidate_id}/answers",
        headers=headers,
        json={"question_key": "work_authorization", "answer": "User-provided answer", "sensitive": True},
    )
    assert answer.status_code == 200
    assert answer.json()["require_confirmation_each_time"] is True


def test_candidate_records_are_not_visible_to_another_user():
    owner_token = create_account("isolation-owner@example.com")
    other_token = create_account("isolation-other@example.com")
    created = client.post(
        "/api/v1/candidates",
        headers=authorization(owner_token),
        json={"display_name": "Private Candidate"},
    )
    candidate_id = created.json()["id"]

    detail = client.get(f"/api/v1/candidates/{candidate_id}", headers=authorization(other_token))
    skill = client.post(
        f"/api/v1/candidates/{candidate_id}/skills",
        headers=authorization(other_token),
        json={"name": "SQL"},
    )

    assert detail.status_code == 404
    assert skill.status_code == 404
    assert all(
        item["id"] != candidate_id
        for item in client.get("/api/v1/candidates", headers=authorization(other_token)).json()
    )
    owner_audit = client.get("/api/v1/audit", headers=authorization(owner_token)).json()
    other_audit = client.get("/api/v1/audit", headers=authorization(other_token)).json()
    assert any(event["entity_id"] == candidate_id and event["action"] == "candidate.created" for event in owner_audit)
    assert all(event["entity_id"] != candidate_id for event in other_audit)


def test_resume_docx_is_extracted_and_requires_review(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.app.services.resumes.settings.upload_root", str(tmp_path))
    token = create_account("resume-owner@example.com")
    headers = authorization(token)
    candidate = client.post("/api/v1/candidates", headers=headers, json={"display_name": "Resume Candidate"}).json()

    document = Document()
    document.add_paragraph("Confirmed only after user review")
    content = io.BytesIO()
    document.save(content)
    uploaded = client.post(
        f"/api/v1/candidates/{candidate['id']}/resumes",
        headers=headers,
        files={
            "file": (
                "master.docx",
                content.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert uploaded.status_code == 201, uploaded.text
    assert uploaded.json()["review_status"] == "needs_review"
    assert "Confirmed only after user review" in uploaded.json()["extracted_text"]
    assert list(tmp_path.rglob("*.docx"))

    master = client.patch(
        f"/api/v1/candidates/{candidate['id']}/resumes/{uploaded.json()['id']}",
        headers=headers,
        json={
            "review_status": "approved",
            "extracted_text": uploaded.json()["extracted_text"],
            "is_master": True,
        },
    )
    assert master.status_code == 200
    assert master.json()["is_master"] is True
    immutable = client.patch(
        f"/api/v1/candidates/{candidate['id']}/resumes/{uploaded.json()['id']}",
        headers=headers,
        json={"review_status": "approved", "extracted_text": "invented replacement"},
    )
    assert immutable.status_code == 409

    duplicate = client.post(
        f"/api/v1/candidates/{candidate['id']}/resumes",
        headers=headers,
        files={
            "file": (
                "master.docx",
                content.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert duplicate.status_code == 409

    deleted = client.delete(f"/api/v1/candidates/{candidate['id']}/resumes/{uploaded.json()['id']}", headers=headers)
    assert deleted.status_code == 204
    assert not list(tmp_path.rglob("*.docx"))


def test_resume_rejects_mismatched_content(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.app.services.resumes.settings.upload_root", str(tmp_path))
    token = create_account("bad-resume@example.com")
    headers = authorization(token)
    candidate = client.post("/api/v1/candidates", headers=headers, json={"display_name": "Bad Resume"}).json()

    response = client.post(
        f"/api/v1/candidates/{candidate['id']}/resumes",
        headers=headers,
        files={"file": ("resume.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 422
    assert not list(tmp_path.rglob("*.*"))


def test_candidate_knowledge_domains_are_user_confirmed():
    token = create_account("knowledge-owner@example.com")
    headers = authorization(token)
    candidate_id = client.post(
        "/api/v1/candidates", headers=headers, json={"display_name": "Knowledge Candidate"}
    ).json()["id"]

    project = client.post(
        f"/api/v1/candidates/{candidate_id}/projects",
        headers=headers,
        json={"name": "Portal modernization", "role": "Business analyst"},
    )
    education = client.post(
        f"/api/v1/candidates/{candidate_id}/education",
        headers=headers,
        json={"institution": "User-provided institution", "degree": None},
    )
    certification = client.post(
        f"/api/v1/candidates/{candidate_id}/certifications",
        headers=headers,
        json={"name": "User-provided certification", "issuer": None},
    )

    assert project.status_code == education.status_code == certification.status_code == 201
    assert project.json()["confirmed"] is True
    assert education.json()["confirmed"] is True
    assert certification.json()["confirmed"] is True


def test_fixture_ingestion_is_owned_audited_and_deduplicated():
    token = create_account("ingestion-owner@example.com")
    other_token = create_account("ingestion-other@example.com")
    headers = authorization(token)
    candidate_id = client.post(
        "/api/v1/candidates", headers=headers, json={"display_name": "Ingestion Candidate"}
    ).json()["id"]
    payload = {
        "provider": "fixture",
        "source_key": "fixture-board",
        "records": [
            {
                "external_id": "job-1",
                "company": "Example Corp",
                "title": "Platform Engineer",
                "location": "Remote",
                "url": "https://jobs.example.com/roles/1?utm_source=test",
                "description": "<p>Build <strong>safe</strong> systems</p>",
                "raw_payload": {"id": "job-1"},
            },
            {
                "external_id": "job-1-alias",
                "company": " Example Corp ",
                "title": "Platform   Engineer",
                "location": "remote",
                "url": "https://jobs.example.com/roles/1?ref=alias",
                "raw_payload": {"id": "job-1-alias"},
            },
        ],
    }

    first = client.post(f"/api/v1/candidates/{candidate_id}/ingestion-runs", headers=headers, json=payload)
    second = client.post(f"/api/v1/candidates/{candidate_id}/ingestion-runs", headers=headers, json=payload)
    hidden = client.get(f"/api/v1/candidates/{candidate_id}/ingestion-runs", headers=authorization(other_token))
    other_headers = authorization(other_token)
    other_candidate_id = client.post(
        "/api/v1/candidates", headers=other_headers, json={"display_name": "Other Ingestion Candidate"}
    ).json()["id"]
    other_run = client.post(
        f"/api/v1/candidates/{other_candidate_id}/ingestion-runs", headers=other_headers, json=payload
    )

    assert first.status_code == 201, first.text
    assert first.json()["discovered_count"] == 2
    assert first.json()["created_count"] == 1
    assert first.json()["duplicate_count"] == 1
    assert second.status_code == 201
    assert second.json()["created_count"] == 0
    assert second.json()["duplicate_count"] == 2
    assert hidden.status_code == 404
    assert other_run.status_code == 201
    assert other_run.json()["created_count"] == 1
    assert all(job["company"] != "Example Corp" for job in client.get("/api/v1/jobs").json())
    audit = client.get(f"/api/v1/audit?candidate_id={candidate_id}", headers=headers).json()
    assert sum(event["action"] == "ingestion.completed" for event in audit) == 2


def test_connector_execution_records_success_and_safe_failure(monkeypatch):
    token = create_account("connector-owner@example.com")
    headers = authorization(token)
    candidate_id = client.post(
        "/api/v1/candidates", headers=headers, json={"display_name": "Connector Candidate"}
    ).json()["id"]

    class SuccessfulConnector:
        def fetch(self, source_key: str) -> list[ExternalJob]:
            return [
                ExternalJob(
                    external_id="connector-1",
                    company=source_key,
                    title="Systems Analyst",
                    location="Remote",
                    url="https://jobs.lever.co/example/connector-1",
                    source="lever",
                    raw_payload={"id": "connector-1"},
                )
            ]

    monkeypatch.setattr("backend.app.services.ingestion.connector_for", lambda provider: SuccessfulConnector())
    success = client.post(
        f"/api/v1/candidates/{candidate_id}/connector-runs",
        headers=headers,
        json={"provider": "lever", "source_key": "example"},
    )

    class FailingConnector:
        def fetch(self, source_key: str) -> list[ExternalJob]:
            raise ConnectorError("upstream_timeout", "The ATS provider timed out", 504)

    monkeypatch.setattr("backend.app.services.ingestion.connector_for", lambda provider: FailingConnector())
    failure = client.post(
        f"/api/v1/candidates/{candidate_id}/connector-runs",
        headers=headers,
        json={"provider": "greenhouse", "source_key": "example"},
    )
    runs = client.get(f"/api/v1/candidates/{candidate_id}/ingestion-runs", headers=headers).json()

    assert success.status_code == 201, success.text
    assert success.json()["status"] == "completed"
    assert success.json()["created_count"] == 1
    assert failure.status_code == 504
    assert "upstream" not in failure.text.casefold()
    assert [run["status"] for run in runs[:2]] == ["failed", "completed"]
    assert runs[0]["error_code"] == "upstream_timeout"
    audit = client.get(f"/api/v1/audit?candidate_id={candidate_id}", headers=headers).json()
    assert any(event["action"] == "ingestion.failed" for event in audit)


def test_saved_source_job_review_provenance_pagination_and_ownership(monkeypatch):
    token = create_account("saved-source-owner@example.com")
    other_token = create_account("saved-source-other@example.com")
    headers = authorization(token)
    candidate_id = client.post(
        "/api/v1/candidates", headers=headers, json={"display_name": "Saved Source Candidate"}
    ).json()["id"]

    class SavedSourceConnector:
        def fetch(self, source_key: str) -> list[ExternalJob]:
            return [
                ExternalJob(
                    external_id="saved-1",
                    company="Saved Example",
                    title="Platform Engineer",
                    location="Remote",
                    url="https://jobs.lever.co/saved/1?utm_source=one",
                    source="lever",
                    raw_payload={"id": "saved-1"},
                ),
                ExternalJob(
                    external_id="saved-alias",
                    company="Saved Example",
                    title="Platform Engineer",
                    location="remote",
                    url="https://jobs.lever.co/saved/1?ref=alias",
                    source="lever",
                    raw_payload={"id": "saved-alias"},
                ),
            ]

    monkeypatch.setattr("backend.app.services.ingestion.connector_for", lambda provider: SavedSourceConnector())
    created = client.post(
        f"/api/v1/candidates/{candidate_id}/sources",
        headers=headers,
        json={"provider": "lever", "source_key": "saved", "label": "Saved board"},
    )
    duplicate = client.post(
        f"/api/v1/candidates/{candidate_id}/sources",
        headers=headers,
        json={"provider": "lever", "source_key": "saved"},
    )
    source_id = created.json()["id"]
    run = client.post(f"/api/v1/candidates/{candidate_id}/sources/{source_id}/run", headers=headers)
    page = client.get(
        f"/api/v1/candidates/{candidate_id}/jobs?provider=lever&q=Platform&limit=1&offset=0",
        headers=headers,
    )
    job_id = page.json()["items"][0]["id"]
    provenance = client.get(f"/api/v1/candidates/{candidate_id}/jobs/{job_id}/provenance", headers=headers)
    reviewed = client.patch(
        f"/api/v1/candidates/{candidate_id}/jobs/{job_id}/decision",
        headers=headers,
        json={"decision": "maybe"},
    )
    hidden = client.get(f"/api/v1/candidates/{candidate_id}/jobs?limit=1", headers=authorization(other_token))
    disabled = client.patch(
        f"/api/v1/candidates/{candidate_id}/sources/{source_id}",
        headers=headers,
        json={"is_enabled": False},
    )
    blocked_run = client.post(f"/api/v1/candidates/{candidate_id}/sources/{source_id}/run", headers=headers)

    assert created.status_code == 201
    assert duplicate.status_code == 409
    assert run.status_code == 201
    assert run.json()["created_count"] == 1
    assert page.status_code == 200
    assert page.json()["total"] == 1
    assert page.json()["limit"] == 1
    assert len(provenance.json()) == 2
    assert all("raw_payload" not in item for item in provenance.json())
    assert reviewed.json()["decision"] == "maybe"
    assert reviewed.json()["status"] == "needs_review"
    assert hidden.status_code == 404
    assert disabled.json()["is_enabled"] is False
    assert blocked_run.status_code == 409
    audit = client.get(f"/api/v1/audit?candidate_id={candidate_id}", headers=headers).json()
    assert any(event["action"] == "job.reviewed" for event in audit)


def test_manual_linkedin_and_indeed_intake_is_normalized_owned_and_idempotent():
    token = create_account("manual-job-owner@example.com")
    other_token = create_account("manual-job-other@example.com")
    headers = authorization(token)
    candidate_id = client.post(
        "/api/v1/candidates", headers=headers, json={"display_name": "Manual Job Candidate"}
    ).json()["id"]
    payload = {
        "url": "https://www.linkedin.com/jobs/view/12345/?trackingId=secret&utm_source=test",
        "company": "Example Company",
        "title": "Product Analyst",
        "location": "Remote",
        "description": "User-confirmed job description",
    }

    first = client.post(f"/api/v1/candidates/{candidate_id}/jobs/manual", headers=headers, json=payload)
    duplicate = client.post(
        f"/api/v1/candidates/{candidate_id}/jobs/manual",
        headers=headers,
        json={**payload, "url": "http://linkedin.com/jobs/view/12345?ref=feed"},
    )
    invalid = client.post(
        f"/api/v1/candidates/{candidate_id}/jobs/manual",
        headers=headers,
        json={**payload, "url": "https://example.com/jobs/12345"},
    )
    hidden = client.get(f"/api/v1/candidates/{candidate_id}/jobs", headers=authorization(other_token))

    assert first.status_code == 201, first.text
    assert first.json()["created"] is True
    assert first.json()["job"]["source"] == "linkedin"
    assert first.json()["job"]["url"] == "https://www.linkedin.com/jobs/view/12345"
    assert duplicate.status_code == 201
    assert duplicate.json()["created"] is False
    assert duplicate.json()["job"]["id"] == first.json()["job"]["id"]
    assert invalid.status_code == 422
    assert hidden.status_code == 404

    provenance = client.get(
        f"/api/v1/candidates/{candidate_id}/jobs/{first.json()['job']['id']}/provenance",
        headers=headers,
    )
    assert provenance.status_code == 200
    assert provenance.json()[0]["provider"] == "linkedin"
    audit = client.get(f"/api/v1/audit?candidate_id={candidate_id}", headers=headers).json()
    assert sum(event["action"] == "job.manually_added" for event in audit) == 2


def test_manual_indeed_intake_preserves_job_key_and_strips_tracking():
    token = create_account("manual-indeed-owner@example.com")
    headers = authorization(token)
    candidate_id = client.post("/api/v1/candidates", headers=headers, json={"display_name": "Indeed Candidate"}).json()[
        "id"
    ]

    response = client.post(
        f"/api/v1/candidates/{candidate_id}/jobs/manual",
        headers=headers,
        json={
            "url": "https://uk.indeed.com/viewjob?jk=abc123&from=search&utm_campaign=test",
            "company": "Indeed Example",
            "title": "Business Analyst",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["job"]["source"] == "indeed"
    assert response.json()["job"]["url"] == "https://www.indeed.com/viewjob?jk=abc123"
