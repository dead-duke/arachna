.PHONY: help install install-dev test test-cov test-cov-html lint format check clean tree info

# Конфигурация
VENV := venv
VENV_BIN := $(VENV)/bin

help:
	@echo "arachna — context collector for AI"
	@echo ""
	@echo "  make install       - install in development mode"
	@echo "  make install-dev   - install with dev dependencies + pre-commit"
	@echo "  make test          - run unit tests"
	@echo "  make test-cov      - run tests with coverage (terminal)"
	@echo "  make test-cov-html - run tests with coverage (HTML)"
	@echo "  make lint          - ruff check"
	@echo "  make format        - ruff format (auto-fix)"
	@echo "  make check         - format + lint + test"
	@echo "  make clean         - remove build artifacts and context files"
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
	ruff check --fix src/ tests/

check: format lint test
	@echo "[OK] All checks passed"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache arachna_context

tree:
	tree -I '__pycache__|*.pyc|*.egg-info|venv|.git|arachna_context' 2>/dev/null || ls -la

info:
	@echo "arachna v$$(python3 -c "from src.arachna import __version__; print(__version__)")"
	@echo "Python: $$(python3 --version)"
	@echo "Path: $$(pwd)"

activate:
	@echo "Activate virtual environment:"
	@echo "  source $(VENV)/bin/activate"
