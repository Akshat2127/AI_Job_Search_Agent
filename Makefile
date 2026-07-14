setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt
	cd frontend && npm install

run:
	uvicorn backend.app.main:app --reload --port 8000

import:
	python scripts/import_jobs.py --csv data/sample_jobs.csv

score:
	python scripts/run_scoring.py

export:
	python scripts/export_google_sheets.py --out output/google_sheets

backend-test:
	.venv/bin/python -m pytest -q

test: backend-test
	npm --prefix frontend test

frontend-dev:
	npm --prefix frontend run dev

frontend-check:
	npm --prefix frontend run lint
	npm --prefix frontend run typecheck
	npm --prefix frontend test
	npm --prefix frontend run build

check: backend-test frontend-check
	docker compose config -q
	git diff --check
