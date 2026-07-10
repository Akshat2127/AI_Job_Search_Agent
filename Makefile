setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt

run:
	uvicorn backend.app.main:app --reload --port 8000

import:
	python scripts/import_jobs.py --csv data/sample_jobs.csv

score:
	python scripts/run_scoring.py

export:
	python scripts/export_google_sheets.py --out output/google_sheets

test:
	pytest
