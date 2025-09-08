.PHONY: help setup install dev test clean docker-build docker-up docker-down backup restore lint format

help:
	@echo "Available commands:"
	@echo "  make setup       - Initial project setup"
	@echo "  make install     - Install dependencies"
	@echo "  make dev         - Run development server"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean temporary files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make backup      - Create backup snapshot"
	@echo "  make restore     - Restore from snapshot"

setup: install
	@cp -n .env.example .env || true
	@mkdir -p data var/index var/logs snapshots
	@python scripts/download_models.py
	@python scripts/migrate_db.py
	@echo "✅ Setup complete! Run 'make dev' to start the server."

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	pytest tests/ -v --cov=app --cov-report=html

lint:
	ruff check app/ cli/ tests/
	mypy app/ cli/ --ignore-missing-imports

format:
	black app/ cli/ tests/
	isort app/ cli/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

backup:
	python cli/main.py admin backup

restore:
	@read -p "Enter snapshot name: " snapshot; \
	python cli/main.py admin restore $$snapshot

watch:
	python cli/main.py ingest watch