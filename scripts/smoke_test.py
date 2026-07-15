"""Run a deterministic migrated in-process application smoke test."""

import os
import subprocess
import sys
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient


def main() -> None:
    with TemporaryDirectory(prefix="jobagent-smoke-") as directory:
        os.environ.update({"APP_ENV": "test", "DATABASE_URL": f"sqlite:///{directory}/smoke.db"})
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, timeout=30)
        from backend.app.main import app

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
