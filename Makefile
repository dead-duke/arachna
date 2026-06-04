.PHONY: help install install-dev test test-cov test-cov-html lint format check clean tree info context diff snapshot-create snapshot-update snapshot-list snapshot-delete store-stats store-gc

VENV := venv
VENV_BIN := $(VENV)/bin
SNAPSHOT ?= cycle-current
PROFILE ?= full

help:
	@echo "arachna — context collector for AI"
	@echo ""
	@echo "Development:"
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
	@echo ""
	@echo "arachna context:"
	@echo "  make context       - collect full context for AI"
	@echo ""
	@echo "Watch (snapshots and diffs):"
	@echo "  make snapshot-create NAME=name  - create named snapshot"
	@echo "  make snapshot-list              - list all snapshots"
	@echo "  make snapshot-update NAME=name  - update existing snapshot"
	@echo "  make snapshot-delete NAME=name  - delete snapshot"
	@echo "  make diff SNAPSHOT=name        - diff from snapshot (auto if one)"
	@echo "  make diff-stat SNAPSHOT=name   - diff stats only"
	@echo "  make store-stats               - store statistics"
	@echo "  make store-gc                  - garbage collect store"

install:
	pip install -e .

install-dev:
	pip install -e .
	pip install -r requirements-dev.txt
	pre-commit install

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v --cov=src/arachna --cov-report=term-missing

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

# ── arachna context ────────────────────────────────────────────────

context:
	arachna --all

# ── Watch commands ──────────────────────────────────────────────────

snapshot-create:
	arachna --snapshot create --profile $(PROFILE) --name $(SNAPSHOT)

snapshot-list:
	arachna --snapshot list

snapshot-update:
	arachna --snapshot update $(SNAPSHOT)

snapshot-delete:
	arachna --snapshot delete $(SNAPSHOT)

diff:
	arachna --diff --from $(SNAPSHOT) $(if $(PROFILE),--profile $(PROFILE))

diff-stat:
	arachna --diff --from $(SNAPSHOT) --stat

store-stats:
	arachna --store stats

store-gc:
	arachna --store gc

