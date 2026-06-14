# Changelog

## v3.4.0 — CLI split + complexity reduction
- cli/ package: 10 handler modules + _helpers.py + COMMAND_HANDLERS registry
- __main__.py: shrink from ~1000 to ~100 lines (build_argparse + dispatch)
- interfaces.py: Tokenizer, ObjectStore, ContentFormatter Protocols
- gatherer.py: decompose _filter_by_query into _score_files, _build_reverse_graph, _expand_import_chain
- watcher.py: decompose _detect_renames_and_moves into _match_exact_renames, _match_similar_renames
- differ_structural.py: _RE_C_LIKE_BLOCK -> _BLOCK_PATTERNS chain (15 single-purpose patterns)
- tests: 11 test files updated, 7 new query pipeline tests, 20 rename matching tests
- 1305 tests, 92% coverage, 0 bugs

## v3.3.0 — Quick wins: DRY, fuzzing, bug fixes
- pack_into_parts: single token-packing primitive in splitter.py
- BUG-001..007: all 7 bugs fixed (streaming profile files, incremental cache, MANIFEST.in, tokenizer safety, file size limit, JSON trailing newline)
- Fuzzing: hypothesis tests for _RE_C_LIKE_BLOCK and _RE_C_LIKE_IMPORT
- Regex timeout protection via _run_with_timeout
- _format_profile_section: deduplicated profile formatting
- _print_compress_stats: deduplicated compression stats printing
- AGPLv3 LICENSE headers on all source files
- 1271 tests, 92% coverage

## v3.2.0 — Benchmarking + Oversized sections + Profile
- Benchmark overhaul: memory, baseline, stress tests, throughput
- Oversized sections: split instead of truncate, continuation markers
- arachna profile command: measure token savings across modes
- 1251 tests, 92% coverage

## v3.1.0 — Plugin system
- Plugin system: environment detector, install/uninstall/list commands
- tree-sitter structural diff for JS/TS/Go
- tiktoken/transformers token counting plugins
- 1233 tests, 92% coverage

## v3.0.0 — CLI redesign
- BREAKING: argparse subparsers replace flat --flag CLI
- Remove cli_watch.py — all handlers in __main__.py
- 1188 tests, 92% coverage

## v2.9.2 — Zero-dep fixes
- Streaming pipeline, config inheritance, snapshot paths, sandbox limits
- TOC indices, collect_api write_to_disk, chars_per_token
- 1124 tests, 92% coverage

## v2.9.1 — Architecture + Code Quality
- Strip strings/comments before brace matching
- 13 code quality fixes
- 1071 tests, 92% coverage

## v2.9.0 — Security hardening
- Two-level command allowlist (restricted vs pre_commands)
- Path traversal protection for snapshot IDs
- Tokenizer top-level statement validation
- TOC section indices, URL scheme validation
- 1071 tests, 92% coverage

## v2.8.2 — Design/UX + Final polish
- --no-pre-commands flag, ARACHNA_SAFE_TOKENIZERS env var
- _EXT_LANG: .hpp, .cmake, .gradle, .lock, .conf
- ARACHNA_PRE_COMMAND_DELAY for rate limiting
- Cross-snapshot pre_commands diff, multi-part diff summary header
- 1043 tests, 93% coverage

## v2.8.1 — Code quality + testability
- 16 LOW fixes: decomposed compute_diff, O(1) file lookup, decision tables
- 1025 tests, 93% coverage

## v2.8.0 — Security + Architecture core
- Log injection fix, RCE find-exec removed
- Single language sets (C_LIKE_LANGS, SCRIPT_LANGS)
- Unified repo-map pipeline
- 1025 tests, 93% coverage

## v2.7.0 — LOW fixes, store, packaging
- 20 LOW/MEDIUM fixes: store, packaging, symlinks, tokenizer, validation
- 998 tests, 1 skipped, 0 failures

## v2.6.0 — Code quality, formatter, differ
- DRY repo-map, pipeline stages, query/mode symmetry
- .tsx/.jsx extensions, PHP use-statements
- Property-based tests (hypothesis), Unicode edge cases
- 998 tests, 0 failures

## v2.5.0 — Security, architecture, watcher
- XML escaping, ast.parse import analysis
- cli_watch.py extraction (~470 lines)
- 970 tests, 93% coverage

## v2.4.0 — Presets update, diff --all
- --presets-update: fetch + merge presets from remote
- --diff --all: full project as diff
- CI: macOS arm64 (macos-14) runner
- 907 tests, 92% coverage

## v2.3.0 — Watch improvements
- Structural diff for pre_commands: line diff for tree/git tag
- Repo-map diff reads full source from store
- 879 tests, 92% coverage

## v2.2.0 — Language presets expansion
- 7 new presets: Go, Rust, Zig, Lua, Elixir, Haskell, Gleam (24 total)
- 833 tests, 92% coverage

## v2.1.0 — Documentation & examples
- docs/TUTORIAL.md: full Agent API tutorial
- examples/delirium_agent.py
- arachna.1 man page
- 816 tests, 0 failures

## v2.0.0 — Agent API + structural diff
- watch.py, collect_api.py, api_types.py, api_errors.py
- differ_structural.py: Python (ast), C-like/script (regex)
- --mode structural for --diff
- 816 tests, 92% coverage

## v1.8.0 — Headers, --query, repo-map mode
- _generate_header for Python, C-like, Ruby/Elixir/Lua
- --query flag with keyword scoring + import chain
- --mode repo-map for signature-only output
- 755 tests, 92% coverage

## v1.7.1 — Unified part numbering
- Always _N even for single part
- Diff files include snapshot name
- 731 tests, 92% coverage

## v1.7.0 — Watch Advanced
- Cross-snapshot diff, rename/move detection, grouped output
- --snapshot info, --snapshot rename, --diff --to, --diff --flat
- 731 tests, 92% coverage

## v1.6.5 — README update
- Updated all Watch commands to v1.6.4 syntax

## v1.6.4 — Watch CLI redesign
- --snapshot: explicit subcommands (list, create, update, delete)
- --diff: writes to files, auto-selects snapshot, --stat
- Removed --full flag
- 654 tests, 92% coverage

## v1.6.3 — Watch command profiles
- pre_commands and command-based profile support
- 654 tests, 92% coverage

## v1.6.2 — Watch polish
- --diff --full, profile files in snapshots
- 619 tests, 92% coverage

## v1.6.1 — PyPI fix
- Fix malformed code fences in PyPI description

## v1.6.0 — Watch MVP
- Content-addressable store (SHA256 + zlib)
- LLM-optimized differ (markdown + XML)
- Watcher orchestration: create_snapshot + compute_diff
- CLI: --snapshot, --diff, --store gc/stats
- 606 tests, 93% coverage

## v1.5.3 — Smart hybrid incremental cache
- mtime_ns + size + SHA256 fast path
- Automatic v1 cache migration
- PyPI publish job on version tags

## v1.5.2 — Race condition fix + escaped pipes
- File locking for merge mode (fcntl/msvcrt/fallback)
- Escaped pipe handling in runner

## v1.5.1 — LOW fixes from audit
- Static completion, direct dispatch, service field removal
- _TEXT_EXTENSIONS from _EXT_LANG
- 478 tests

## v1.5.0 — Architecture refactor + LOW fixes
- PRESETS dict -> individual JSON files
- Decompose collect(), CHARS_PER_TOKEN removal
- 467 tests, 94% coverage

## v1.4.4 — Security allowlist cleanup
- Remove mkdir, xargs, sed, awk, tee from _ALLOWED_COMMANDS
- 455 tests

## v1.4.3 — Unreal Engine preset
- AGPLv3 license

## v1.4.2 — Audit LOW fixes + compression stats bug
- Fix compression stats, atomic writes, tokenizer safety docs

## v1.4.1 — Unified split + audit fixes
- Remove pre_split_mode, unified section list via split_sections()
- 418 tests

## v1.4.0 — Security hardening + cleanup
- Remove fallback to sys.modules, chmod/chown from allowlist
- 418 tests

## v1.3.0 — Multi-source split modes + bug fixes
- pre_split_mode/pre_split_marker, BUG-001 and BUG-004 fixes
- 392 tests, 93%

## v1.2.2 — CLI consistency
- --preset in interactive mode, test coverage
- 384 tests

## v1.2.1 — Security fix
- Tokenizer sandbox hardening, preset validation
- 384 tests

## v1.2.0 — Presets as config
- External presets.json support, load_presets_from_file()
- 384 tests

## v1.1.0 — Language & engine presets
- 12 presets: Python, JS/TS, Godot, Unity, C/C++, C#, Swift, Kotlin/Java, Ruby, PHP, Docker, Terraform
- 29 new tests

## v1.0.2 — --version fix
- --version works without profile argument

## v1.0.1 — Windows test fixes
- Cross-platform test stability

## v1.0.0 — Stable release
- 256 tests, 90% coverage

## v0.9.4 — Final polish
- _assemble_content pipeline, module-level imports

## v0.9.3 — Final fixes
- _cmd_validate profile isolation, test mock fixes

## v0.9.2 — Final audit fixes
- hook.py .git check, gitignore symlink handling

## v0.9.1 — Coverage
- 30 new tests, 256 tests, 90% coverage

## v0.9.0 — Infrastructure
- PyPI packaging, GitHub Actions CI, MANIFEST.in

## v0.8.5 — Sandbox
- dry_run parameter, interactive confirmation

## v0.8.4 — Merge
- --merge flag for --profile

## v0.8.3 — Git hooks
- install_hook() for post-commit git hook

## v0.8.2 — Doctor
- run_doctor() validates config and gitignore integrity

## v0.8.1 — Low fixes
- DEFAULT_EXCLUDE programmatic, tokenizer passthrough

## v0.8.0 — Decompose _collect_named_sections
- Extract _collect_directory_sections, _collect_file_sections

## v0.7.5 — Truncation API + shlex
- Replace print() with logger.warning()

## v0.7.4 — Sandbox pipe fix
- Validate each pipe part individually

## v0.7.3 — Test stability
- os.chdir -> tmp_path/monkeypatch, mock subprocess

## v0.7.2 — Architecture cleanup
- Remove global _TOKENIZE, unify EXCLUDED_DIRS

## v0.7.1 — Critical fixes
- Remove interpreters from _ALLOWED_COMMANDS

## v0.7.0 — Major refactor
- Remove global state, atomic manifest writes

## v0.6.0 — Pluggable tokenizer
- load_tokenizer(spec), custom tokenizer support

## v0.5.0 — Tests, safety, audit fixes
- Shell security warning, 175 tests, 90% coverage

## v0.4.2 — Audit fixes
- Removed unused code, CJK token tests

## v0.4.1 — Table of contents + manifest
- TOC in each part, chat-manifest.md

## v0.4.0 — Shell completion, post_commands hooks
- completion.py, post_commands in profile

## v0.3.0 — Compress, incremental, section_format
- Whitespace compression, incremental mode, xml/json output

## v0.2.2 — Git split marker
- per-profile manifest cleanup

## v0.2.1 — arachna init
- Interactive .arachna.json bootstrap

## v0.2.0 — Single file output
- chat-code.md, .arachna_manifest.json, 129 tests, 90% coverage

## v0.1.5 — Shebang detection
- Python, bash, node, ruby, perl

## v0.1.4 — Tests, coverage, bugfixes
- 102 tests, 65% coverage

## v0.1.3 — Validate, gitignore, default profile
- validator.py, gitignore.py

## v0.1.2 — Dry-run, renderer, pre-commit, ruff
- --dry-run, --output-dir, --verbose

## v0.1.1 — Tests + fixes
- 29 tests: tokenizer, splitter, config, formatter

## v0.1.0 — MVP
- tokenizer, runner, formatter, splitter, gatherer, collector, config, CLI
