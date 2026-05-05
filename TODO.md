# TODO

## v0.1.0 — MVP

- [x] tokenizer.py — conservative token count (4 chars ≈ 1 token)
- [x] config.py — load .arachna.json, find_config() upwards
- [x] collector.py — orchestrator: gather → split → write
- [x] gatherer.py — collect files, pre_commands, command output
- [x] splitter.py — 4 split modes, atomic sections
- [x] formatter.py — file formatting, lang detection (ext + filename), exclude check
- [x] runner.py — shlex.split() for safe execution, shell=True fallback
- [x] _FILENAME_LANG — Dockerfile, Makefile, .env, Procfile, Vagrantfile
- [x] exclude_patterns with fnmatch
- [x] DEFAULT_EXCLUDE (__pycache__, *.pyc, .git, venv, node_modules, .DS_Store)
- [x] __main__.py — CLI: --profile, --all, --clean, --list
- [x] pyproject.toml — pip install -e .
- [x] __init__.py with __version__
- [x] .gitignore
- [x] README.md with install, usage, config fields, split modes
- [x] CHANGELOG.md
- [x] Git tag v0.1.0

## v0.1.1 — Dry-run & Developer Experience

- [x] --dry-run: show what will be collected with real split simulation
- [x] renderer.py: aligned output with per-section token tracking
- [x] --output-dir <path>: override output_dir from CLI
- [x] --verbose: show skipped files
- [x] Makefile: test, test-cov, lint, format, clean
- [x] pre-commit: ruff + unit tests
- [x] requirements-dev.txt: ruff, pytest, pytest-cov, pre-commit
- [x] Ruff config in pyproject.toml
- [x] Git tag v0.1.1

## v0.2.0 — Quality

### Tests
- [ ] tests/test_runner.py — run_command with mocked subprocess
- [ ] tests/test_gatherer.py — dry_run with multiple parts
- [ ] tests/test_splitter.py — split() integration tests
- [ ] tests/test_renderer.py — output format verification

### Features
- [ ] --validate: check config for errors, exit code 1, contextual messages
- [ ] --estimate: alias for --dry-run
- [ ] .gitignore-aware collection: auto-exclude gitignored patterns
- [ ] Default profile when profiles is empty: *.py, *.md, *.yaml, *.toml, *.json

## v0.3.0 — Smart Features

- [ ] Shebang detection for lang_for_path
- [ ] Whitespace compression mode (--compress)
- [ ] Single file output mode (--single)
- [ ] Incremental collection: cache mtime, only update changed files
- [ ] section_format: markdown, xml, json presets

## v0.4.0 — Extensibility

- [ ] include_binary with base64 encoding + size limit
- [ ] Tagged sections: `<file path="..." language="...">...</file>`
- [ ] Custom template for file sections
- [ ] Hooks: pre_collect, post_collect, per_file
- [ ] Plugin system for custom collectors
- [ ] Shell completion (bash, zsh, fish)
- [ ] arachna init: bootstrap .arachna.json interactively

## Backlog

- [ ] pip install arachna (publish to PyPI)
- [ ] CI/CD (GitHub Actions)
- [ ] Support pyproject.toml [tool.arachna] as config source
- [ ] Watch mode (re-collect on file changes)
