# Changelog

## v0.2.2 — Git split marker, per-profile manifest cleanup

- git split_marker: \n=== COMMIT: (was \n\n=== COMMIT:)
- --all: clean all files, rebuild all profiles
- --profile: clean only this profile, keep others in manifest
- _cmd_single: proper KeyError handling
- init.py: correct git marker for defaults and interactive

## v0.2.1 — arachna init

- --init: interactive .arachna.json bootstrap
- --init --defaults: auto-detect profiles
- Scans: src/, app/, tests/, docs/, data/prompts/, config/
- Supports: Python, JS/TS, Go, Rust projects

## v0.2.0 — Single file output, manifest, test reorg

- Single file output (chat-code.md, not chat-code_1.md)
- Manifest (.arachna_manifest.json) for cleanup between runs
- Default output_dir: arachna_context/
- Test reorg: 25 files, one test per file
- CLI refactored into _cmd_* functions
- 129 tests, 90% coverage

## v0.1.5 — Shebang Detection
- formatter.py: shebang detection, 107 tests, 66% coverage

## v0.1.4 — Tests & Bugfixes
- 102 tests, 65% coverage, binary file detection

## v0.1.3 — Validate & Gitignore
- validator.py, gitignore.py, default profile, 46 tests

## v0.1.2 — Dry-run, renderer, pre-commit, ruff
- dry_run, renderer, Makefile, pre-commit, requirements-dev.txt

## v0.1.1 — Tests + fixes
- 29 tests: tokenizer, splitter, config, formatter

## v0.1.0 — MVP
- tokenizer, runner, formatter, splitter, gatherer, collector, config, CLI
- 4 split modes, exclude_patterns, _FILENAME_LANG
- pip install -e . ready
