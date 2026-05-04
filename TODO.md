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

## v0.2.0 — Quality & Usability

### Quality
- [ ] tests/test_tokenizer.py — count_tokens edge cases (empty, CJK, emoji)
- [ ] tests/test_splitter.py — _build_parts boundary tests (single > limit, exact fit)
- [ ] tests/test_config.py — get_profile defaults, missing profile, merge behavior
- [ ] tests/test_formatter.py — lang_for_path (ext, filename, shebang), is_excluded

### Features
- [ ] --dry-run: show what will be collected with token estimates, no files written
- [ ] --output-dir <path>: override output_dir from CLI
- [ ] --verbose: show skipped files (binary, no permission, empty)
- [ ] --estimate: show token usage per file with visual bar, highlight files >20% of limit
- [ ] --validate: exit code 1 on errors, contextual messages with hints
- [ ] Shebang detection for lang_for_path (#!/usr/bin/env python3 → python)
- [ ] Whitespace compression mode (--compress / compress: true in profile)
- [ ] Default profile when profiles is empty: collect *.py, *.md, *.yaml, *.toml, *.json
- [ ] .gitignore-aware collection: auto-exclude gitignored files in addition to exclude_patterns
- [ ] Single file output mode (--single / single_file: true)
- [ ] Docstrings for all public functions with examples

## v0.3.0 — Performance & Flexibility

- [ ] Incremental collection: cache mtime, only update changed files
- [ ] section_format: markdown, xml, json presets
- [ ] include_binary with base64 encoding + size limit
- [ ] Tagged sections: `<file path="..." language="...">...</file>`
- [ ] Custom template for file sections (header/footer per file)

## v0.4.0 — Extensibility

- [ ] Hooks: pre_collect, post_collect, per_file
- [ ] Plugin system for custom collectors
- [ ] Shell completion (bash, zsh, fish)
- [ ] arachna init: bootstrap .arachna.json interactively

## Backlog

- [ ] pip install arachna (publish to PyPI)
- [ ] CI/CD (GitHub Actions)
- [ ] Support pyproject.toml [tool.arachna] as config source
- [ ] Watch mode (re-collect on file changes)
