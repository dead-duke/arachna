.PHONY: help install install-dev test test-cov test-cov-html lint format check clean tree info context diff diff-stat snapshot-create snapshot-list snapshot-update snapshot-delete store-stats store-gc trailing-ws fix-trailing-ws

VENV := venv
VENV_BIN := $(VENV)/bin
SNAPSHOT ?= cycle
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
	@echo "  make check         - format + lint + test + trailing-ws"
	@echo "  make clean         - remove build artifacts and context files"
	@echo "  make tree          - show project structure"
	@echo "  make info          - show project info"
	@echo ""
	@echo "Quality:"
	@echo "  make trailing-ws   - check for trailing whitespace and double blank lines at EOF"
	@echo "  make fix-trailing-ws - automatically fix trailing whitespace and double blank lines"
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

trailing-ws:
	@echo "Checking for trailing whitespace..."
	@! grep -rn '[[:space:]]$$' README.md CHANGELOG.md TODO.md docs/ --include='*.md' || (echo "ERROR: Trailing whitespace found" && exit 1)
	@echo "Checking for double blank lines at EOF..."
	@for f in README.md CHANGELOG.md TODO.md $$(find docs -name '*.md' 2>/dev/null); do \
		if [ -f "$$f" ] && [ $$(wc -l < "$$f") -gt 0 ]; then \
			if [ "$$(tail -1 "$$f")" = "" ] && [ "$$(tail -2 "$$f" | head -1)" = "" ]; then \
				echo "ERROR: $$f ends with double blank line"; exit 1; \
			fi; \
		fi; \
	done
	@echo "OK: no trailing whitespace or double blank lines"

fix-trailing-ws:
	@echo "Fixing trailing whitespace and double blank lines at EOF..."
	@python3 -c 'import pathlib, sys; files = ["README.md", "CHANGELOG.md", "TODO.md"] + [str(p) for p in pathlib.Path("docs").rglob("*.md")]; [exec("p = pathlib.Path(f); c = p.read_text(); c = \"\\n\".join(l.rstrip() for l in c.split(\"\\n\")); c = c.rstrip(\"\\n\") + \"\\n\"; p.write_text(c)") or print(f"{f}: fixed") for f in files if pathlib.Path(f).exists()]'
	@echo "Done."

check: format lint test trailing-ws
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
	arachna --diff --from $(SNAPSHOT)

diff-stat:
	arachna --diff --from $(SNAPSHOT) --stat

store-stats:
	arachna --store stats

store-gc:
	arachna --store gc

