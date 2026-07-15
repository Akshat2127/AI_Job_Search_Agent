from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app


def test_browser_cookie_requires_csrf_for_mutations(monkeypatch):
    monkeypatch.setattr(settings, "auth_mode", "password")
    with TestClient(app) as client:
        registration = client.post(
            "/api/v1/auth/register",
            json={"email": "browser-session@example.com", "password": "correct horse battery staple"},
        )
        assert registration.status_code == 201
        login = client.post(
            "/api/v1/auth/browser-login",
            json={"email": "browser-session@example.com", "password": "correct horse battery staple"},
        )
        assert login.status_code == 200
        cookies = login.headers.get_list("set-cookie")
        assert any(
            "jobagent_session=" in cookie and "HttpOnly" in cookie and "SameSite=strict" in cookie for cookie in cookies
        )
        csrf_token = client.cookies.get(settings.csrf_cookie_name)
        assert csrf_token

        rejected = client.post("/api/v1/candidates", json={"display_name": "CSRF rejected"})
        accepted = client.post(
            "/api/v1/candidates",
            headers={settings.csrf_header_name: csrf_token},
            json={"display_name": "CSRF accepted"},
        )
        assert rejected.status_code == 403
        assert accepted.status_code == 201

        logout = client.post("/api/v1/auth/logout", headers={settings.csrf_header_name: csrf_token})
        assert logout.status_code == 204
        assert client.get("/api/v1/auth/me").status_code == 401


def test_bearer_clients_do_not_require_csrf(monkeypatch):
    monkeypatch.setattr(settings, "auth_mode", "password")
    with TestClient(app) as client:
        client.post(
            "/api/v1/auth/register",
            json={"email": "bearer-session@example.com", "password": "correct horse battery staple"},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "bearer-session@example.com", "password": "correct horse battery staple"},
        )
        token = login.json()["access_token"]
        created = client.post(
            "/api/v1/candidates",
            headers={"Authorization": f"Bearer {token}"},
            json={"display_name": "Bearer candidate"},
        )
        assert created.status_code == 201
