# Changelog

## v0.2.0 — Single file output, manifest, test reorg

- Single file output mode (chat-code.md instead of chat-code_1.md)
- Manifest (.arachna_manifest.json) for cleanup between runs
- Default output_dir: arachna_context/
- Test reorganization: 25 test files, one test per file
- CLI refactored into _cmd_* functions
- 129 tests, 90% coverage

## v0.1.5 — Shebang Detection

- formatter.py: detect language from shebang
- Supports: python, bash, node, ruby, perl
- Extension wins over shebang for .py .sh files
- 107 tests, 66% coverage

## v0.1.4 — Tests & Bugfixes

- 102 tests (up from 46), 65% coverage (up from 25%)
- gatherer.py: deduplicated with _collect_named_sections
- renderer.py: 100% coverage
- formatter.py: binary file detection (null bytes)
- gitignore.py: skip venv/.gitignore and hidden dirs
- tests: gatherer (18), renderer (10), gitignore (6), splitter (23), formatter (15), config (5)

## v0.1.3 — Validate & Gitignore

- validator.py: check split_mode, max_tokens, content source, split_marker
- gitignore.py: parse .gitignore patterns for auto-exclusion
- Default profile when .arachna.json has no profiles
- CLI: --validate flag, exit code 1 on errors
- test_validator.py: 10 tests
- test_runner.py: 7 tests
- renderer: <0.1% for very small percentages
- git profile added to .arachna.json

## v0.1.2 — Dry-run, renderer, pre-commit, ruff

- gatherer.dry_run: real split simulation with per-section token tracking
- renderer: aligned output with = for sections, - for parts
- --dry-run, --output-dir, --verbose CLI flags
- Makefile: test, test-cov, lint, format, clean
- pre-commit: ruff + unit tests
- ruff config in pyproject.toml
- requirements-dev.txt: ruff, pytest, pytest-cov, pre-commit

## v0.1.1 — Tests + fixes

- 29 tests: tokenizer, splitter, config, formatter
- Fixed _split_to_sections: .strip() removed, preserves leading newlines
- Fixed test_config: mock find_config, resolve() for macOS /var symlink

## v0.1.0 — MVP

- tokenizer, runner, formatter, splitter, gatherer, collector, config, CLI
- 4 split modes: by_file, by_paragraph, by_marker, single
- exclude_patterns with fnmatch + DEFAULT_EXCLUDE
- _FILENAME_LANG for Dockerfile, Makefile, .env, Procfile
- shlex.split() for safe command execution
- pip install -e . ready
