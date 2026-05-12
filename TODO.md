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
- [x] compress, incremental, section_format, include_binary, 140 tests

## v0.4.0 — Shell completion + hooks
- [x] bash/zsh completion, post_commands, 144 tests

## v0.4.1 — Table of contents + manifest
- [x] TOC in each part, chat-manifest.md

## v0.4.2 — Audit fixes
- [x] Removed dead code, fixed CJK tests, README token margin

## v0.5.0 — Tests, safety, audit, tokenizer prep
- [x] Removed compress_indent (unsafe), safe compression only
- [x] Shell security warning in README
- [x] LICENSE file (MIT)
- [x] formatter: verbose skip reasons
- [x] splitter: separator for xml/json
- [x] Tests: cache, completion, init, formatter, incremental, manifest
- [x] .arachna.json: "all" profile (32768 tokens)
- [x] pyproject.toml: classifiers, readme, license
- [x] 175 tests, 90% coverage

## v0.6.0 — Pluggable tokenizer
- [ ] load_tokenizer(spec) in tokenizer.py
- [ ] tokenizer field in profile (default: "default")
- [ ] Plumb tokenizer through collector → gatherer → splitter
- [ ] Tests for custom tokenizer plugin

## v0.7.0 — Additional tests
- [ ] Coverage ≥ 95%
- [ ] Integration tests for --format xml/json output
- [ ] Edge cases: empty files, huge files, symlinks

## v1.0.0 — Public release
- [ ] pip install arachna (publish to PyPI)
- [ ] arachna install-hook (git post-commit)

## Backlog
- [ ] CI/CD (GitHub Actions)
