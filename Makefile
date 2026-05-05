.PHONY: help install install-dev test test-cov test-cov-html lint format clean tree info

help:
	@echo "arachna — context collector for AI"
	@echo ""
	@echo "  make install       - install in development mode"
	@echo "  make install-dev   - install with dev dependencies + pre-commit"
	@echo "  make test          - run unit tests"
	@echo "  make test-cov      - run tests with coverage (terminal)"
	@echo "  make test-cov-html - run tests with coverage (HTML)"
	@echo "  make lint          - ruff check"
	@echo "  make format        - ruff format"
	@echo "  make clean         - remove build artifacts and chat-*.md"
	@echo "  make tree          - show project structure"
	@echo "  make info          - show project info"

install:
	pip install -e .

install-dev:
	pip install -e .
	pip install -r requirements-dev.txt
	pre-commit install

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=src/arachna --cov-report=term-missing

test-cov-html:
	python -m pytest tests/ --cov=src/arachna --cov-report=html
	@echo "[OK] Report: htmlcov/index.html"

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache
	rm -f chat-*.md

tree:
	tree -I '__pycache__|*.pyc|*.egg-info|venv|.git' 2>/dev/null || ls -la

info:
	@echo "arachna v0.1.0"
	@echo "Python: $$(python3 --version)"
	@echo "Path: $$(pwd)"
