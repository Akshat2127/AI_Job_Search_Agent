import os
import sqlite3
import subprocess
import sys

import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings


def test_production_rejects_sqlite_and_console_logging():
    with pytest.raises(ValidationError, match="production requires PostgreSQL"):
        Settings(_env_file=None, app_env="production", database_url="sqlite:///unsafe.db", log_format="json")

    with pytest.raises(ValidationError, match="production requires LOG_FORMAT=json"):
        Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://user:pass@db/jobagent",
            log_format="console",
        )


def test_initial_migration_upgrades_empty_database(tmp_path):
    database = tmp_path / "migration.db"
    environment = os.environ.copy()
    environment.update({"APP_ENV": "test", "DATABASE_URL": f"sqlite:///{database}"})

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=os.getcwd(),
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    with sqlite3.connect(database) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    assert {
        "jobs",
        "users",
        "candidate_profiles",
        "resumes",
        "education",
        "certifications",
        "project_experiences",
        "audit_events",
        "ingestion_runs",
        "job_source_records",
        "alembic_version",
    }.issubset(tables)
    assert revision == ("20260714_0003",)
