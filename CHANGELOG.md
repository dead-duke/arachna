# Changelog

## v0.3.0 — Compress, incremental, formats, binary

- Whitespace compression: blank lines, trailing ws, indent (--compress)
- Incremental collection: mtime cache, skip unchanged files (--incremental)
- section_format: markdown (default), xml, json (--format)
- include_binary: base64 encoding with size/extension filters
- 140 tests (up from 129)

## v0.2.2 — Git split marker, per-profile manifest cleanup

- git split_marker: \\n=== COMMIT: (was \\n\\n=== COMMIT:)
- --all: clean all files, rebuild all profiles
- --profile: clean only this profile, keep others in manifest

## v0.2.1 — arachna init

- --init: interactive .arachna.json bootstrap
- --init --defaults: auto-detect profiles for Python/JS/Go/Rust

## v0.2.0 — Single file output, manifest, test reorg

- Single file output (chat-code.md), manifest, arachna_context/
- 129 tests, 90% coverage

## v0.1.5 — Shebang Detection
## v0.1.4 — Tests & Bugfixes
## v0.1.3 — Validate & Gitignore
## v0.1.2 — Dry-run, renderer, pre-commit
## v0.1.1 — Tests + fixes
## v0.1.0 — MVP
