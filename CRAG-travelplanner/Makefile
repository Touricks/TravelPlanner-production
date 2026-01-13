.PHONY: help install test lint format check clean run

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make run         - Start CRAG API server (port 8000)"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters (ruff)"
	@echo "  make format      - Format code (black)"
	@echo "  make check       - Run all checks (format + lint + test)"
	@echo "  make clean       - Clean cache and build files"

run:
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	uvicorn seekdb_agent.api.main:app --reload --port 8000

install:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=seekdb_agent --cov-report=term-missing

lint:
	ruff check seekdb_agent/ tests/
	mypy seekdb_agent/

format:
	black seekdb_agent/ tests/
	ruff check --fix seekdb_agent/ tests/

check: format lint test
	@echo "✅ All checks passed!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache .ruff_cache
