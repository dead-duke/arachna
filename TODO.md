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
- [x] DEFAULT_EXCLUDE
- [x] __main__.py — CLI: --profile, --all, --clean, --list
- [x] pyproject.toml — pip install -e .
- [x] __init__.py with __version__
- [x] .gitignore
- [x] README.md
- [x] CHANGELOG.md

## v0.1.1 — Tests + fixes

- [x] tests/test_tokenizer.py — 9 tests
- [x] tests/test_splitter.py — 9 tests
- [x] tests/test_config.py — 4 tests
- [x] tests/test_formatter.py — 7 tests
- [x] Fixed _split_to_sections: .strip() → removed
- [x] Fixed test_config: mock find_config, resolve() for macOS /var symlink

## v0.1.2 — Dry-run & Developer Experience

- [x] gatherer.dry_run: real split simulation with per-section token tracking
- [x] renderer.py: aligned output with = for sections, - for parts
- [x] --dry-run, --output-dir, --verbose CLI flags
- [x] Makefile: test, test-cov, lint, format, clean
- [x] pre-commit: ruff + unit tests
- [x] requirements-dev.txt

## v0.1.3 — Validate & Gitignore

- [x] validator.py: check split_mode, max_tokens, content source, split_marker
- [x] CLI: --validate flag, exit code 1 on errors
- [x] gitignore.py: parse .gitignore patterns for auto-exclusion
- [x] Default profile when .arachna.json has no profiles
- [x] tests/test_validator.py — 10 tests
- [x] tests/test_runner.py — 7 tests
- [x] renderer: <0.1% for very small percentages
- [x] git profile in .arachna.json

## v0.1.4 — Tests & Bugfixes

- [x] tests/test_gatherer.py — 18 tests
- [x] tests/test_renderer.py — 10 tests
- [x] tests/test_gitignore.py — 6 tests
- [x] tests/test_splitter.py — 23 tests
- [x] tests/test_formatter.py — 15 tests
- [x] tests/test_config.py — 5 tests
- [x] Binary file detection (null bytes)
- [x] Gitignore: skip venv/.* dirs
- [x] gatherer.py: deduplicated with _collect_named_sections
- [x] 102 tests, 65% coverage

## v0.1.5 — Shebang Detection

- [x] formatter.py: _lang_from_shebang, _SHEBANG_MAP
- [x] Supports: python, bash, node, ruby, perl
- [x] Extension wins over shebang
- [x] 107 tests, 66% coverage

## v0.2.0 — Single file output, manifest, test reorg (current)

- [x] Single file output mode (chat-code.md, not chat-code_1.md)
- [x] Manifest (.arachna_manifest.json) for cleanup between runs
- [x] Default output_dir: arachna_context/
- [x] Test reorganization: 25 files, one test per file
- [x] CLI refactored into _cmd_* functions
- [x] 129 tests, 90% coverage
- [ ] arachna init: bootstrap .arachna.json interactively, create arachna_context/
- [ ] Update CHANGELOG
- [ ] Git tag v0.2.0

## v0.3.0 — Features

- [ ] Whitespace compression mode (--compress)
- [ ] Incremental collection: cache mtime
- [ ] section_format: markdown, xml, json presets
- [ ] include_binary with base64 encoding

## v0.4.0 — Extensibility

- [ ] Tagged sections
- [ ] Hooks: pre_collect, post_collect, per_file
- [ ] Plugin system
- [ ] Shell completion (bash, zsh, fish)

## Backlog

- [ ] pip install arachna (publish to PyPI)
- [ ] CI/CD (GitHub Actions)
- [ ] Support pyproject.toml [tool.arachna] as config source
- [ ] Watch mode (re-collect on file changes)
