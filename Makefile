setup:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt
	cd frontend && npm install

run:
	uvicorn backend.app.main:app --reload --port 8000

migrate:
	.venv/bin/alembic upgrade head

import:
	python scripts/import_jobs.py --csv data/sample_jobs.csv

score:
	python scripts/run_scoring.py

export:
	python scripts/export_google_sheets.py --out output/google_sheets

backend-test:
	.venv/bin/python -m pytest -q

backend-check: backend-test
	.venv/bin/ruff check backend tests scripts playwright
	.venv/bin/ruff format --check backend tests scripts playwright
	.venv/bin/mypy backend/app
	.venv/bin/python -m scripts.smoke_test

test: backend-test
	npm --prefix frontend test

frontend-dev:
	npm --prefix frontend run dev

preprod-up:
	docker compose -f docker-compose.yml -f docker-compose.preprod.yml up --build --detach

preprod-down:
	docker compose -f docker-compose.yml -f docker-compose.preprod.yml down

frontend-check:
	npm --prefix frontend run lint
	npm --prefix frontend run typecheck
	npm --prefix frontend test
	npm --prefix frontend run build

check: backend-check frontend-check
	docker compose config -q
	docker compose -f docker-compose.yml -f docker-compose.preprod.yml config -q
	git diff --check
