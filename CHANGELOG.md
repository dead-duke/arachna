# Changelog

## v4.0.0 — Layered architecture
- src/arachna/ restructured into domain/, watch/, plugins/, api/, config/
- All lazy imports eliminated, cyclic dependencies resolved
- cli/ package: 10 handler modules + _helpers.py + COMMAND_HANDLERS registry
- __main__.py: shrink from ~1000 to ~100 lines
- interfaces.py: Tokenizer, ObjectStore, ContentFormatter Protocols
- language_dispatch.py: HEADER_PARSERS + BLOCK_PARSERS, get_header_parser/get_block_parser
- gatherer decomposed: gatherer_core + gatherer_query + gatherer_strategies + facade
- _BLOCK_PATTERNS chain: 15 single-purpose patterns replace _RE_C_LIKE_BLOCK
- atomic_write.py: atomic_write_text/bytes, store + collector use atomic write
- Tests restructured to mirror src/arachna/ layout
- _make_profile deduplicated into tests/conftest.py
- 1499 tests, 95% coverage

## v3.6.0 — Data pipeline: manifest API + metrics + unlimited tokens + parallel I/O
- arachna manifest --json: machine-readable manifest for AI agents
- PipelineMetrics dataclass + CollectResult.metrics
- .arachna_metrics.json: extract/transform/load times + file/token counts
- max_tokens=0 unlimited mode
- compute_diff streaming=True parameter
- ThreadPoolExecutor parallel I/O (ARACHNA_MAX_WORKERS=1 default, opt-in)
- Progress to stderr for large collections
- root parameter required throughout entire codebase
- 1429 tests, 93% coverage, 0 os.chdir

## v3.5.0 — Ecosystem: testability, CI, docs, man page, ADR
- find_config/load_config: explicit root parameter
- store/gatherer/collector tests: 0 monkeypatch.chdir
- runner.py: run_pre_commands try-except, max_output_size parameter
- tokenizer.py: lazy plugins, env vars via functions not globals
- presets.py: fetch_presets timeout, schema validation
- gatherer.py: Strategy pattern for mode dispatch
- importlib.reload: removed from test code
- ADR: 15 architecture decision records in docs/adr/
- Man page: arachna.1 updated to v3.5.0 with ENVIRONMENT section
- CI: benchmark workflow, pdoc deploy to GitHub Pages
- README: Security section, API Reference link

## v3.4.0 — CLI split + complexity reduction
- cli/ package: 10 handler modules + _helpers.py + COMMAND_HANDLERS registry
- __main__.py: shrink from ~1000 to ~100 lines (build_argparse + dispatch)
- interfaces.py: Tokenizer, ObjectStore, ContentFormatter Protocols
- gatherer.py: decompose _filter_by_query into _score_files, _build_reverse_graph, _expand_import_chain
- watcher.py: decompose _detect_renames_and_moves into _match_exact_renames, _match_similar_renames
- differ_structural.py: _RE_C_LIKE_BLOCK -> _BLOCK_PATTERNS chain (15 single-purpose patterns)
- 1305 tests, 92% coverage

## v3.3.0 — Quick wins: DRY, fuzzing, bug fixes
- pack_into_parts: single token-packing primitive in splitter.py
- BUG-001..007: all 7 bugs fixed
- Fuzzing: hypothesis tests, regex timeout protection
- AGPLv3 LICENSE headers on all source files
- 1271 tests, 92% coverage

## v3.2.0 — Benchmarking + Oversized sections + Profile
- Benchmark overhaul, oversized sections split, arachna profile command
- 1251 tests, 92% coverage

## v3.1.0 — Plugin system
- Plugin system, tree-sitter structural diff, tiktoken/transformers
- 1233 tests, 92% coverage

## v3.0.0 — CLI redesign
- argparse subparsers replace flat --flag CLI
- 1188 tests, 92% coverage

## v2.9.2 — Zero-dep fixes
- Streaming pipeline, config inheritance, snapshot paths, sandbox limits
- 1124 tests, 92% coverage

## v2.9.1 — Architecture + Code Quality
- 13 code quality fixes, 1071 tests

## v2.9.0 — Security hardening
- Two-level command allowlist, path traversal protection, tokenizer validation
- 1071 tests, 92% coverage

## v2.8.2 — Design/UX + Final polish
- --no-pre-commands, ARACHNA_SAFE_TOKENIZERS, multi-part diff header
- 1043 tests, 93% coverage

## v2.8.1 — Code quality + testability
- 16 LOW fixes, 1025 tests

## v2.8.0 — Security + Architecture core
- Log injection fix, single language sets, unified repo-map
- 1025 tests, 93% coverage

## v2.7.0 — LOW fixes, store, packaging
- 20 LOW/MEDIUM fixes, 998 tests

## v2.6.0 — Code quality, formatter, differ
- DRY repo-map, .tsx/.jsx, PHP use-statements, hypothesis
- 998 tests

## v2.5.0 — Security, architecture, watcher
- XML escaping, ast.parse import analysis, cli_watch.py extraction
- 970 tests, 93% coverage

## v2.4.0 — Presets update, diff --all
- --presets-update, --diff --all, CI macOS arm64
- 907 tests, 92% coverage

## v2.3.0 — Watch improvements
- Structural diff for pre_commands, repo-map diff from store
- 879 tests, 92% coverage

## v2.2.0 — Language presets expansion
- 7 new presets: Go, Rust, Zig, Lua, Elixir, Haskell, Gleam
- 833 tests, 92% coverage

## v2.1.0 — Documentation & examples
- TUTORIAL.md, delirium_agent.py, arachna.1
- 816 tests

## v2.0.0 — Agent API + structural diff
- watch.py, collect_api.py, api_types.py, api_errors.py, differ_structural.py
- 816 tests, 92% coverage

## v1.8.0 — Headers, --query, repo-map mode
- 755 tests, 92% coverage

## v1.7.1 — Unified part numbering
- 731 tests

## v1.7.0 — Watch Advanced
- Cross-snapshot diff, rename/move detection, grouped output
- 731 tests, 92% coverage

## v1.6.5 — README update
## v1.6.4 — Watch CLI redesign
- 654 tests, 92% coverage
## v1.6.3 — Watch command profiles
## v1.6.2 — Watch polish
## v1.6.1 — PyPI fix
## v1.6.0 — Watch MVP
- Content-addressable store, LLM-optimized differ, watcher
- 606 tests, 93% coverage

## v1.5.3 — Smart hybrid incremental cache
## v1.5.2 — Race condition fix + escaped pipes
## v1.5.1 — LOW fixes from audit
## v1.5.0 — Architecture refactor
- 467 tests, 94% coverage
## v1.4.4 — Security allowlist cleanup
## v1.4.3 — Unreal Engine preset, AGPLv3
## v1.4.2 — Audit LOW fixes
## v1.4.1 — Unified split
## v1.4.0 — Security hardening
## v1.3.0 — Multi-source split modes
- 392 tests, 93%
## v1.2.2 — CLI consistency
## v1.2.1 — Security fix
## v1.2.0 — Presets as config
## v1.1.0 — Language & engine presets
## v1.0.2 — --version fix
## v1.0.1 — Windows test fixes
## v1.0.0 — Stable release
- 256 tests, 90% coverage
## v0.9.4 — Final polish
## v0.9.3 — Final fixes
## v0.9.2 — Final audit fixes
## v0.9.1 — Coverage
## v0.9.0 — Infrastructure
## v0.8.5 — Sandbox
## v0.8.4 — Merge
## v0.8.3 — Git hooks
## v0.8.2 — Doctor
## v0.8.1 — Low fixes
## v0.8.0 — Decompose _collect_named_sections
## v0.7.5 — Truncation API + shlex
## v0.7.4 — Sandbox pipe fix
## v0.7.3 — Test stability
## v0.7.2 — Architecture cleanup
## v0.7.1 — Critical fixes
## v0.7.0 — Major refactor
## v0.6.0 — Pluggable tokenizer
## v0.5.0 — Tests, safety, audit fixes
- 175 tests, 90% coverage
## v0.4.2 — Audit fixes
## v0.4.1 — Table of contents + manifest
## v0.4.0 — Shell completion, post_commands
## v0.3.0 — Compress, incremental, section_format
## v0.2.2 — Git split marker
## v0.2.1 — arachna init
## v0.2.0 — Single file output
- 129 tests, 90% coverage
## v0.1.5 — Shebang detection
## v0.1.4 — Tests, coverage, bugfixes
## v0.1.3 — Validate, gitignore, default profile
## v0.1.2 — Dry-run, renderer, pre-commit, ruff
## v0.1.1 — Tests + fixes
## v0.1.0 — MVP
