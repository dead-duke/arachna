# TODO

## v0.1.0 — MVP
- [x] tokenizer, config, collector, gatherer, splitter, formatter, runner, CLI
- [x] pip install -e . ready

## v0.1.1 — Tests + fixes
- [x] 29 tests, fixed splitter and config

## v0.1.2 — Dry-run & Developer Experience
- [x] dry_run, renderer, --dry-run, --output-dir, --verbose
- [x] Makefile, pre-commit, ruff, requirements-dev.txt

## v0.1.3 — Validate & Gitignore
- [x] validator.py, gitignore.py, default profile
- [x] --validate flag, tests (46 total)

## v0.1.4 — Tests & Bugfixes
- [x] 102 tests, 65% coverage, deduplicated gatherer
- [x] Binary file detection, gitignore fixes

## v0.1.5 — Shebang Detection
- [x] formatter.py: shebang detection
- [x] 107 tests, 66% coverage

## v0.2.0 — Single file output, manifest, test reorg
- [x] Single file output (chat-code.md, not _1.md)
- [x] Manifest (.arachna_manifest.json) for cleanup
- [x] Default output_dir: arachna_context/
- [x] Test reorg: 25 files, one test per file
- [x] CLI refactored into _cmd_* functions
- [x] 129 tests, 90% coverage

## v0.2.1 — arachna init
- [x] --init: interactive bootstrap
- [x] --init --defaults: auto-detect profiles
- [x] Scans: src/, app/, tests/, docs/, data/prompts/, config/
- [x] Supports: Python, JS/TS, Go, Rust projects

## v0.2.2 — Git split marker, per-profile manifest cleanup
- [x] git split_marker: \\n=== COMMIT: (was \\n\\n=== COMMIT:)
- [x] --all: clean all files, rebuild all profiles
- [x] --profile: clean only this profile, keep others in manifest
- [x] _cmd_single: proper KeyError handling
- [x] init.py: correct git marker for defaults and interactive

## v0.3.0 — Features
- [ ] Whitespace compression mode (--compress)
- [ ] Incremental collection: cache mtime
- [ ] section_format: markdown, xml, json presets
- [ ] include_binary with base64 encoding

## v0.4.0 — Extensibility
- [ ] Tagged sections, hooks, plugin system
- [ ] Shell completion, arachna init improvements

## Backlog
- [ ] pip install arachna (publish to PyPI)
- [ ] CI/CD (GitHub Actions)
- [ ] Support pyproject.toml [tool.arachna] as config source
