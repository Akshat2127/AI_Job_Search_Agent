import io

from docx import Document
from fastapi.testclient import TestClient

from backend.app.main import app

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
