# Changelog

## v0.1.3 — Validate, gitignore, default profile, runner tests

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

## v0.1.5 — Shebang Detection

- formatter.py: detect language from shebang (#!... → python/bash/node)
- Supports: python, bash, node, ruby, perl
- Extension wins over shebang for .py .sh files
- 5 new tests, 107 total, 66% coverage
