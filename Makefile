.PHONY: help install install-dev test test-cov test-cov-html lint format check clean tree info context diff diff-stat snapshot-create snapshot-list snapshot-update snapshot-delete store-stats store-gc trailing-ws fix-trailing-ws benchmark

PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo python3)
PYTEST ?= $(PYTHON) -m pytest
PIP ?= $(PYTHON) -m pip

VENV := venv
VENV_BIN := $(VENV)/bin
SNAPSHOT := cycle
PROFILE ?= full

# ── Python Scripts ─────────────────────────────────────────────────

define FIX_WS_PYTHON
import pathlib

EXCLUDE_DIRS = {'venv', '.venv', '.git', '__pycache__', '.tox', 'htmlcov', '.ruff_cache', 'arachna_context', 'build', 'dist', '.pytest_cache', '.coverage', 'node_modules'}
EXTENSIONS = {'.py', '.md', '.txt', '.yml', '.yaml', '.sh', '.json', '.toml', '.cfg', '.ini', '.rst'}
NO_EXT_FILES = {'Makefile', 'Dockerfile', 'LICENSE', 'MANIFEST.in'}

def get_files():
    for p in pathlib.Path('.').rglob('*'):
        if p.is_file():
            if any(part in EXCLUDE_DIRS for part in p.parts):
                continue
            if p.suffix in EXTENSIONS or p.name in NO_EXT_FILES or p.name.startswith('requirements'):
                yield p

fixed_count = 0
for p in get_files():
    try:
        content = p.read_text()
        if not content:
            continue
        lines = [line.rstrip() for line in content.split('\n')]
        new_content = '\n'.join(lines)
        new_content = new_content.rstrip('\n') + '\n'

        if new_content != content:
            p.write_text(new_content)
            print(f'Fixed: {p}')
            fixed_count += 1
    except UnicodeDecodeError:
        continue

print(f'Total fixed: {fixed_count}')
endef
export FIX_WS_PYTHON

define CHECK_WS_PYTHON
import pathlib, sys

EXCLUDE_DIRS = {'venv', '.venv', '.git', '__pycache__', '.tox', 'htmlcov', '.ruff_cache', 'arachna_context', 'build', 'dist', '.pytest_cache', '.coverage', 'node_modules'}
EXTENSIONS = {'.py', '.md', '.txt', '.yml', '.yaml', '.sh', '.json', '.toml', '.cfg', '.ini', '.rst'}
NO_EXT_FILES = {'Makefile', 'Dockerfile', 'LICENSE', 'MANIFEST.in'}

def get_files():
    for p in pathlib.Path('.').rglob('*'):
        if p.is_file():
            if any(part in EXCLUDE_DIRS for part in p.parts):
                continue
            if p.suffix in EXTENSIONS or p.name in NO_EXT_FILES or p.name.startswith('requirements'):
                yield p

has_error = False
for p in get_files():
    try:
        content = p.read_text()
        if not content:
            continue

        for line in content.split('\n'):
            if line != line.rstrip():
                print(f'ERROR: {p} has trailing whitespace on line')
                has_error = True
                break

        if content.endswith('\n\n'):
            print(f'ERROR: {p} ends with multiple blank lines')
            has_error = True

    except UnicodeDecodeError:
        continue

if has_error:
    sys.exit(1)
endef
export CHECK_WS_PYTHON

# ── Help & Setup ───────────────────────────────────────────────────

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
	@echo "  make check         - format + lint + fix-trailing-ws + trailing-ws + test"
	@echo "  make clean         - remove build artifacts and context files"
	@echo "  make tree          - show project structure"
	@echo "  make info          - show project info"
	@echo ""
	@echo "Quality:"
	@echo "  make trailing-ws     - check for trailing whitespace and double blank lines at EOF"
	@echo "  make fix-trailing-ws - automatically fix trailing whitespace and double blank lines"
	@echo ""
	@echo "Benchmarks:"
	@echo "  make benchmark     - run performance benchmarks"
	@echo ""
	@echo "arachna context:"
	@echo "  make context       - collect full context for AI"
	@echo ""
	@echo "Watch (snapshots and diffs):"
	@echo "  make snapshot-create SNAPSHOT=name  - create named snapshot (default: cycle)"
	@echo "  make snapshot-list                  - list all snapshots"
	@echo "  make snapshot-update SNAPSHOT=name  - update existing snapshot (default: cycle)"
	@echo "  make snapshot-delete SNAPSHOT=name  - delete snapshot"
	@echo "  make diff SNAPSHOT=name             - diff from snapshot (default: cycle)"
	@echo "  make diff-stat SNAPSHOT=name        - diff stats only (default: cycle)"
	@echo "  make store-stats                    - store statistics"
	@echo "  make store-gc                       - garbage collect store"

install:
	$(PIP) install -e .

install-dev: install
	$(PIP) install -r requirements-dev.txt
	pre-commit install

# ── Testing & Linting ──────────────────────────────────────────────

test:
	$(PYTEST) tests/ -v

test-cov:
	$(PYTEST) tests/ -v --cov=src/arachna --cov-report=term-missing

test-cov-html:
	$(PYTEST) tests/ --cov=src/arachna --cov-report=html
	@echo "[OK] Report: htmlcov/index.html"

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# ── Quality & Whitespace ───────────────────────────────────────────

trailing-ws:
	@echo "Checking for trailing whitespace and EOF issues across the entire project..."
	@$(PYTHON) -c "$$CHECK_WS_PYTHON"
	@echo "OK: no trailing whitespace or double blank lines"

fix-trailing-ws:
	@echo "Fixing trailing whitespace and double blank lines at EOF..."
	@$(PYTHON) -c "$$FIX_WS_PYTHON"
	@echo "Done."

check: format lint fix-trailing-ws trailing-ws test
	@echo "[OK] All checks passed"

# ── Cleanup & Info ─────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache arachna_context build dist *.egg-info

tree:
	tree -I '__pycache__|*.pyc|*.egg-info|venv|.git|arachna_context|build|dist' 2>/dev/null || ls -la

info:
	@echo "arachna v$$($(PYTHON) -c "from src.arachna import __version__; print(__version__)")"
	@echo "Python: $$($(PYTHON) --version)"
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
	arachna --diff --from $(SNAPSHOT)

diff-stat:
	arachna --diff --from $(SNAPSHOT) --stat

store-stats:
	arachna --store stats

store-gc:
	arachna --store gc

# ── Benchmarks ─────────────────────────────────────────────────────

benchmark:
	$(PYTEST) tests/benchmark/ -v -s
