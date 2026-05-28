# Changelog

## v0.7.1 — Critical fixes

- Removed interpreters (python, node, ruby, perl, php) from _ALLOWED_COMMANDS
- Fixed tokenizer passthrough in _build_parts (keyword args)
- Fixed _apply_args_to_profile mutation (returns copy)

## v0.7.0 — Security sandbox, architecture cleanup

- Sandbox validation: _validate_command with _BLOCKED_PATTERNS and _ALLOWED_COMMANDS
- Command audit logging to .arachna_commands.log
- Atomically written cache via tempfile + os.replace
- Gitignore: size limits, EXCLUDED_DIRS filtering, binary detection
- Formatter: size check before read_text, verbose skip reasons
- Refactored _cmd_all and _cmd_single via shared _run_profile
- Deprecated global _TOKENIZE in gatherer (set_tokenizer/get_tokenizer kept for compat)
- 179 tests, 90% coverage

## v0.6.0 — Pluggable tokenizer

- load_tokenizer(spec) in tokenizer.py
- tokenizer field in profile
- Plumbed through collector → gatherer
- 179 tests, 90% coverage

## v0.5.0 — Tests, safety, audit fixes

- Tests for incremental mode (cache + changed/new/deleted)
- Tests for manifest cleanup
- Tests for completion.py, init.py, formatter xml/json
- Removed compress_indent (unsafe for Python)
- Safe compression: blank lines + trailing spaces only
- Shell security warning in README
- LICENSE file (MIT)
- 175 tests, 90% coverage

## v0.4.2 — Audit fixes

- Removed dead code in gatherer.py
- Fixed CJK token tests
- README: token margin recommendation

## v0.4.1 — Table of contents + manifest

- TOC in each part: lists files
- chat-manifest.md: summary of all collected files

## v0.4.0 — Shell completion + hooks

- Bash and zsh completion (arachna --completion bash|zsh)
- post_commands in profile: run after collection
- 144 tests, 70% coverage

## v0.3.0 — Compress, incremental, formats, binary

- Whitespace compression (--compress)
- Incremental collection: mtime cache (--incremental)
- section_format: markdown (default), xml, json (--format)
- include_binary: base64 encoding with size/extension filters
- 140 tests

## v0.2.2 — Git split marker, per-profile manifest cleanup

- git split_marker: \n=== COMMIT:
- --all: clean all files, rebuild all profiles
- --profile: clean only this profile

## v0.2.1 — arachna init

- --init interactive + --defaults auto-detect

## v0.2.0 — Single file output, manifest, test reorg

- Single file output, manifest, 129 tests, 90% coverage

## v0.1.5 — Shebang Detection
## v0.1.4 — Tests & Bugfixes
## v0.1.3 — Validate & Gitignore
## v0.1.2 — Dry-run, renderer, pre-commit
## v0.1.1 — Tests + fixes
## v0.1.0 — MVP
