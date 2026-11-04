# EduSphere — convenience targets. Run `make help` for a list.

PYTHON ?= python3
PORT   ?= 8080

.PHONY: help frontend serve build data test db-up db-down db-schema db-seed backend clean

help:
	@echo "EduSphere — The Paper Archive"
	@echo ""
	@echo "  make frontend   Open the built site with a local web server (port $(PORT))"
	@echo "  make serve      Same as frontend"
	@echo "  make build      Rebuild frontend/index.html from src/"
	@echo "  make data       Regenerate src/data/archive.json from source datasets"
	@echo "  make test       Playwright browser smoke test (needs playwright + chromium)"
	@echo "  make db-up      Start a local PostgreSQL (docker compose)"
	@echo "  make db-down    Stop the local PostgreSQL"
	@echo "  make db-schema  Apply database/schema.postgres.sql"
	@echo "  make db-seed    Apply database/seed_data.postgres.sql"
	@echo "  make backend    Run the FastAPI app with --reload"
	@echo "  make clean      Remove Python cache files"

frontend serve:
	cd frontend && $(PYTHON) serve.py $(PORT)

build:
	cd frontend && $(PYTHON) build.py

data:
	cd frontend && $(PYTHON) build_data.py

test:
	cd frontend && $(PYTHON) validate.py

db-up:
	docker compose up -d db

db-down:
	docker compose down

db-schema:
	psql "$(DATABASE_URL)" -f database/schema.postgres.sql

db-seed:
	psql "$(DATABASE_URL)" -f database/seed_data.postgres.sql

backend:
	cd backend && uvicorn app:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
