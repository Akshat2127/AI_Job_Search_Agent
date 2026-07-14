"""Run a deterministic in-process application smoke test."""

from fastapi.testclient import TestClient

from backend.app.main import app


def main() -> None:
    with TestClient(app) as client:
        checks = {
            "/api/v1/health": client.get("/api/v1/health"),
            "/api/v1/readiness": client.get("/api/v1/readiness"),
            "/api/v1/jobs": client.get("/api/v1/jobs"),
        }
    failures = {path: response.status_code for path, response in checks.items() if response.status_code != 200}
    if failures:
        raise SystemExit(f"Smoke test failed: {failures}")
    print("Smoke test passed: health, readiness, and jobs API are available")


if __name__ == "__main__":
    main()
