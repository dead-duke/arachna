# TODO

## v0.1.0 — MVP
- [x] tokenizer, config, collector, gatherer, splitter, formatter, runner, CLI

## v0.1.1 — Tests + fixes
- [x] 29 tests

## v0.1.2 — Dry-run & Developer Experience
- [x] dry_run, renderer, Makefile, pre-commit

## v0.1.3 — Validate & Gitignore
- [x] validator, gitignore, default profile

## v0.1.4 — Tests & Bugfixes
- [x] 102 tests, 65% coverage

## v0.1.5 — Shebang Detection
- [x] shebang detection, 107 tests

## v0.2.0 — Single file output, manifest, test reorg
- [x] chat-code.md, manifest, arachna_context/, 129 tests, 90% coverage

## v0.2.1 — arachna init
- [x] --init interactive + --defaults auto-detect

## v0.2.2 — Git split marker, per-profile manifest cleanup
- [x] \\n=== COMMIT: marker, --profile keeps other profiles

## v0.3.0 — Compress, incremental, formats, binary
- [x] Whitespace compression (--compress)
- [x] Incremental collection (--incremental)
- [x] section_format: markdown, xml, json (--format)
- [x] include_binary with base64 encoding
- [x] 140 tests

## v0.4.0 — Extensibility
- [ ] Tagged sections: <file path="..." language="...">...</file>
- [ ] Hooks: pre_collect, post_collect, per_file
- [ ] Plugin system for custom collectors
- [ ] Shell completion (bash, zsh, fish)
- [ ] arachna init improvements (more project types)

## Backlog
- [ ] pip install arachna (publish to PyPI)
- [ ] CI/CD (GitHub Actions)
- [ ] Support pyproject.toml [tool.arachna] as config source
- [ ] Watch mode (re-collect on file changes)
