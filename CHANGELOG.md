# Changelog

## v3.3.0 — Quick wins: DRY, fuzzing, bug fixes

- pack_into_parts: single token-packing primitive in splitter.py replaces 4 duplicates
- BUG-001..007: all 7 bugs fixed (streaming files, incremental cache, MANIFEST.in, merge_presets tokenizer, write_object atomicity, file size limit, trailing newline in JSON)
- _format_profile_section: deduplicated profile formatting in _cmd_snapshot_info
- _print_compress_stats: deduplicated compress stats printing in gatherer.py
- _arachna() helper moved to tests/integration/conftest.py (7 files updated)
- Fuzzing: hypothesis tests for _RE_C_LIKE_BLOCK and _RE_C_LIKE_IMPORT with ReDoS protection
- Timeout: _run_with_timeout for regex operations in differ_structural.py
- Collector: comment explaining dict.fromkeys dedup idiom
- _cmd_collect_list: warning on KeyError instead of silent skip
- AGPLv3 LICENSE headers added to all .py files
- Security: docs/SECURITY.md with full architecture documentation
- Security: SECURITY.md with vulnerability reporting policy
- 1271 tests, 92% coverage, 0 bugs

## v3.2.0 — Benchmarking + Oversized sections + Profile

- Benchmark overhaul: memory measurement, baseline tracking, warm-up, throughput, stress tests
- Oversized sections fix: _split_oversized_section with paragraph->line->character fallback
- Continuation markers (CONTINUES/CONTINUED) for split sections
- _build_toc deduplicates indices and shows [split across N parts]
- arachna profile command: measures token savings across all modes
- 1251 tests, 92% coverage

## v3.1.0 — Plugin system

- Plugin system with tree-sitter and tiktoken support
- plugins.py: environment detector, install/uninstall/list commands
- Lazy import for tree-sitter in differ_structural.py with fallback
- Lazy import for tiktoken/transformers in tokenizer.py with fallback
- Per-language extras in pyproject.toml (javascript, typescript, go, tiktoken, all)
- Core stays zero-dep, all plugins optional
- 1233 tests, 92% coverage, 0 bugs

## v3.0.0 — CLI redesign with argparse subparsers

- BREAKING: CLI redesign with argparse subparsers (collect, snapshot, diff, store, plugins, presets, doctor, init, completion)
- Remove cli_watch.py, all manual sys.argv parsing
- Plugin stubs for v3.1
- 1188 tests, 92% coverage, 0 bugs

## v2.9.2 — Zero-dep fixes + Streaming pipeline

- Streaming full mode: pre_commands -> query filter -> compress -> pack, O(max_tokens) memory
- TOC: split_sections returns indices, no substring matching
- Config: extends field with typed merge (scalars override, exclude append, sources replace)
- Snapshots: relative paths from project root via find_config()
- Sandbox: Popen with chunked read, max_output_size via ARACHNA_MAX_OUTPUT_SIZE
- Tokenizer: chars_per_token in profile, ARACHNA_CHARS_PER_TOKEN env
- API: collect() 3-tuple, collect_api write_to_disk=False, parts from memory
- Cache: _collect_import_graph per file list
- Runner: always returns str, shell=True in Popen
- 1124 tests, 2 skipped, 92% coverage, 0 bugs

## v2.9.1 — Architecture + Code Quality fixes

- MEDIUM ARCH-01: Strip strings/comments before brace matching
- LOW CQ-02 to CQ-15: 13 code quality fixes
- 1071 tests, 92% coverage, 0 bugs

## v2.9.0 — Security hardening

- HIGH: Two-level command allowlist (restricted vs pre_commands modes)
- HIGH: Path traversal protection via validate_snapshot_id()
- HIGH: Tokenizer top-level statement validation
- MEDIUM: TOC section indices, URL scheme validation
- LOW: Double header fix, pattern traversal, atomic write_object
- 1071 tests, 92% coverage, 0 bugs

## v2.8.2 — Design/UX + Final polish

- --no-pre-commands CLI flag
- ARACHNA_SAFE_TOKENIZERS env var
- _EXT_LANG: .hpp, .cmake, .gradle, .lock, .conf
- ARACHNA_PRE_COMMAND_DELAY for rate limiting
- Cross-snapshot pre_commands diff with removed lines
- Multi-part diff summary header with change counts
- _load_builtin_presets mtime-based cache invalidation
- store.py atomic write for .arachna/.gitignore
- 1043 tests, 93% coverage, 0 bugs

## v2.8.1 — Code quality + testability

- LOW: 16 code quality + testability fixes
- watcher: decomposed compute_diff, O(1) file lookup, same-ext rename detect
- differ_structural: named groups in _RE_C_LIKE_BLOCK
- formatter: decision table, truncation fix
- gatherer: command+directories warning, pre_commands filtered in query
- runner: injectable _write_log
- store: _store_root explicit root parameter
- 1025 tests, 93% coverage, 0 bugs

## v2.8.0 — Security + Architecture core

- HIGH: log injection fix + RCE find-exec removed
- MEDIUM: single language sets, unified repo-map, deduplicated compute_diff
- MEDIUM: tokenizer passthrough, DRY helpers, @lru_cache config
- 1025 tests, 93% coverage, 0 bugs

## v2.7.0 — LOW fixes, store, packaging, polish

- 20 LOW/MEDIUM fixes: store, packaging, symlinks, tokenizer, validation
- PEP 639 license, optional-dependencies, env-configurable cache
- 998 tests, 1 skipped, 0 failures

## v2.6.0 — Code quality, formatter, differ, test coverage

- Code quality: DRY repo-map, pipeline stages, query/mode symmetry
- Formatter: .tsx/.jsx, PHP use-statements, import a,b fix
- Differ: token limit for added files, Go type name fix
- TOC: section indices instead of content matching
- Presets: @lru_cache, UTF-16 error handling
- Tests: property-based (hypothesis), Unicode edges, msvcrt mock
- 998 tests, 1 skipped, 0 failures

## v2.5.0 — Security, architecture, watcher fixes

- HIGH: XML escaping in differ.py
- HIGH: ast.parse import analysis for local tokenizer files
- Architecture: cli_watch.py extraction (~470 lines)
- Watcher: normalize_path, path_matches_profile, pre_commands diff
- 970 tests, 93% coverage

## v2.4.0 — Presets update, diff --all, merge_lock tests

- --presets-update: fetch + merge presets from remote
- --diff --all: full project as diff (no snapshot needed)
- fetch_presets + merge_presets in presets.py
- merge_lock tests for fcntl + msvcrt (Windows)
- CI: add macOS arm64 (macos-14) runner
- 907 tests, 92% coverage

## v2.3.0 — Watch improvements

- Structural diff for pre_commands: line diff for tree/git tag
- Repo-map diff reads full source from store
- BUG-001 and BUG-002 fixed
- 879 tests, 92% coverage

## v2.2.0 — Language presets expansion

- 7 new presets: Go, Rust, Zig, Lua, Elixir, Haskell, Gleam (24 total)
- formatter.py: new language extensions
- 833 tests, 92% coverage

## v2.1.0 — Documentation & examples

- docs/TUTORIAL.md: full Agent API tutorial
- examples/delirium_agent.py: Delirium agent integration
- arachna.1: man page
- README.md: Programmatic API section

## v2.0.0 — Agent API + structural diff

- Agent API: watch.py, collect_api.py, api_types.py, api_errors.py
- Structural diff: differ_structural.py (ast + regex)
- --mode structural for --diff
- Repo-map fix: signatures from raw text
- 816 tests, 92% coverage

## v1.8.0 — Headers, --query, repo-map mode

- Headers: _generate_header for Python, C-like, Ruby/Elixir/Lua
- --query flag with keyword scoring + import chain
- --mode repo-map for signature-only output
- 755 tests, 92% coverage

## v1.7.1 — Unified part numbering + diff file naming

- Unified part numbering: always _N even for single part
- Diff files include snapshot name: chat-diff-{snapshot}_N.md
- Cross-snapshot naming: chat-diff-{from}-to-{to}_N.md
- 731 tests, 92% coverage

## v1.7.0 — Watch Advanced

- Cross-snapshot diff, rename/move detection, grouped output
- --snapshot info, --snapshot rename
- --diff --to, --diff --flat

## v1.6.5 — README update for Watch CLI

- README.md: updated all Watch commands to v1.6.4 syntax

## v1.6.4 — Watch CLI redesign

- --snapshot: explicit subcommands (list, create, update, delete)
- --diff: writes to files, auto-selects snapshot, --stat
- store.py: manifest stores full profile dict, update_snapshot
- collector.py: _write_diff_parts for token-split diff
- Removed --full flag
- 654 tests, 92% coverage

## v1.6.3 — Watch command profiles

- store.py/watcher.py: pre_commands and command-based profile support
- 9 new tests for command profiles

## v1.6.2 — Watch polish

- watcher.py: create_snapshot and compute_diff include profile files
- __main__.py: --diff --full for combined full context + diff
- 619 tests, 92% coverage

## v1.6.1 — PyPI README fix

- README.md: fix malformed code fences in PyPI description

## v1.6.0 — Watch MVP

- Content-addressable store with SHA256 + zlib
- LLM-optimized differ (markdown + XML)
- Watcher orchestration: create_snapshot + compute_diff
- CLI: --snapshot, --diff, --store gc/stats
- 606 tests, 93% coverage

## v1.5.3 — Smart hybrid incremental cache

- Smart hybrid incremental cache: mtime_ns + size + SHA256
- Fast path skips unchanged files without hashing
- Automatic v1 cache migration
- PyPI publish job on version tags

## v1.5.2 — Race condition fix + escaped pipes

- collector.py: file-based locking for merge concurrent safety
- runner.py: escaped pipes (\|) and backslash in double-quoted strings

## v1.5.1 — LOW fixes from audit

- gatherer.py: tokenizer required parameter in _collect_named_sections
- __main__.py: direct if-elif dispatch in main()
- completion.py: static completion without dynamic profile listing
- presets: remove unused service field from all JSON files
- formatter.py: _TEXT_EXTENSIONS generated from _EXT_LANG

## v1.5.0 — Architecture refactor + LOW fixes

- Split PRESETS dict into individual JSON files in presets/ directory
- Remove _SERVICE_PRESETS hardcoded set
- Decompose collect() into _write_parts() and _run_post_commands()
- Remove CHARS_PER_TOKEN dead code from splitter.py
- 467 tests, 94% coverage

## v1.4.4 — Security allowlist cleanup

- Remove mkdir, xargs, sed, awk, tee from _ALLOWED_COMMANDS
- All commands now strictly read-only

## v1.4.3 — Unreal Engine preset

- Add "unreal" preset: Source/, Content/, *.cpp, *.h, *.cs, *.ini, *.uproject, *.uplugin
- AGPLv3 license switch from MIT

## v1.4.2 — Audit LOW fixes + compression stats bug

- gatherer.py: fix compression stats — raw_tokens from named_sections, comp_tokens from compressed sections
- runner.py: remove touch from _ALLOWED_COMMANDS
- tokenizer.py: document safety check order in _is_safe_tokenizer docstring

## v1.4.1 — Unified split + audit fixes

- gatherer.py: remove pre_split_mode/pre_split_marker, unified section list via split_sections()
- splitter.py: add split_sections() for dense packing of pre-built sections
- runner.py: remove mv, cp from _ALLOWED_COMMANDS

## v1.4.0 — Security hardening + cleanup

- tokenizer.py: remove fallback to sys.modules in _is_safe_tokenizer, deny by default
- runner.py: remove chmod, chown from _ALLOWED_COMMANDS
- gatherer.py: skip symlinks in _scan_directories with warning

## v1.3.0 — Multi-source split modes + bug fixes

- gatherer.py: pre_split_mode/pre_split_marker for separate pre_commands splitting
- runner.py: _split_pipe_parts respects shell quoting (BUG-001 fix)
- runner.py: word-boundary matching for _BLOCKED_PATTERNS word group (BUG-001 fix)
- presets.py: c_cpp detect reduced to CMakeLists.txt only (BUG-004 fix)

## v1.2.2 — CLI consistency for --preset in interactive mode

- init.py: run_interactive passes preset to detect_presets, filters autodetection to single preset

## v1.2.1 — Security fix for importlib sandbox and preset validation

- tokenizer.py: hardened _is_safe_tokenizer with expanded _SUSPICIOUS_MODULES set
- presets.py: unified _is_safe_tokenizer — delegates to tokenizer.py

## v1.2.0 — Presets as config

- presets.py: load_presets_from_file() for external presets.json with validation
- presets.py: get_all_presets() — merge built-in and external presets
- __main__.py: --preset argument for --init

## v1.1.0 — Language & engine presets

- presets.py: presets (Python, JS/TS, Godot, Unity, C/C++, C#, Swift, Kotlin/Java, Ruby, PHP, Docker, Terraform)
- init.py: rewritten on presets.py
- formatter.py: extended _EXT_LANG

## v1.0.2 — --version works without profile argument

- __main__.py: handle --version before argparse like --completion

## v1.0.1 — Windows test fixes

- tests: cross-platform fixes for cache, formatter, gatherer, hook

## v1.0.0 — First stable release

- Public API, CLI, 24 presets, Watch subsystem, streaming pipeline
- 1251 tests, 92% coverage

## v0.9.4 — Final polish

- runner.py: move import json to module level
- gatherer.py: extract _assemble_content shared pipeline

## v0.9.3 — Final fixes

- __main__.py: _cmd_validate uses get_profile() for each profile
- cache.py, gitignore.py: comments explaining constants

## v0.9.2 — Final audit fixes

- hook.py: check .git is a directory (is_dir)
- doctor.py: check project_root.is_dir() before gitignore scan
- gitignore.py: handle ValueError from relative_to (symlinks outside root)

## v0.9.1 — Coverage

- 30 new tests: runner, collector, formatter, cache
- Coverage: 85% to 90% (256 tests)

## v0.9.0 — Infrastructure

- pyproject.toml: authors, keywords, urls, classifiers
- MANIFEST.in for PyPI packaging
- GitHub Actions CI workflow (ubuntu, windows, macos x python 3.11-3.14)

## v0.8.5 — Sandbox

- dry_run parameter to run_command(): unsafe commands shown but not executed
- Interactive confirmation for unsafe commands in dry-run mode

## v0.8.4 — Merge

- --merge flag for --profile: appends to existing output instead of replacing

## v0.8.3 — Git hooks

- hook.py: install_hook() for post-commit git hook installation

## v0.8.2 — Doctor

- doctor.py: run_doctor() validates config and gitignore integrity

## v0.8.1 — Low fixes

- Generate DEFAULT_EXCLUDE programmatically from _COMMON_EXCLUDE_DIRS
- Add tests for custom tokenizer passthrough

## v0.8.0 — Decompose _collect_named_sections

- Extract _collect_directory_sections with incremental logic
- Extract _collect_file_sections for explicitly listed files

## v0.7.5 — Truncation API + shlex

- Replace print() with logger.warning() for was_truncated
- Handle shlex.split ValueError with explicit warning

## v0.7.4 — Sandbox pipe fix

- Validate each pipe part individually in _validate_command

## v0.7.3 — Test stability

- Replace os.chdir with tmp_path/monkeypatch in all test modules (14 files)
- Mock subprocess.run in runner tests

## v0.7.2 — Architecture cleanup

- Remove global _TOKENIZE, get_tokenizer, set_tokenizer from gatherer.py
- Unify EXCLUDED_DIRS between config.py and gitignore.py

## v0.7.1 — Critical fixes

- Remove interpreters from _ALLOWED_COMMANDS (CRITICAL)
- Fix tokenizer passthrough in _build_parts — use keyword args
- Fix _apply_args_to_profile mutation — return copy instead of mutating original

## v0.7.0 — Atomic manifest writes

- collector.py: atomic save_manifest via tempfile + os.replace

## v0.6.0 — Pluggable tokenizer

- tokenizer.py: load_tokenizer(spec) for custom tokenizers

## v0.5.0 — Tests, safety, audit fixes

- Removed compress_indent (unsafe for Python), safe compression only
- LICENSE file (MIT)
- 175 tests, 90% coverage

## v0.4.2 — Audit fixes, README, TODO update

- Removed unused list comprehension in gatherer.py
- Fixed CJK token tests

## v0.4.1 — Table of contents + manifest

- TOC in each part: lists files with part N of M
- chat-manifest.md: summary of all collected files

## v0.4.0 — Shell completion, post_commands hooks

- completion.py: bash and zsh completion
- post_commands in profile: run commands after files are written

## v0.3.0 — Compress, incremental, section_format, include_binary

- Whitespace compression: blank lines, trailing ws, indent
- Incremental collection: mtime cache, skip unchanged
- section_format: markdown (default), xml, json
- include_binary: base64 encoding with size/extension filters

## v0.2.2 — Git split marker, per-profile manifest cleanup

- git split_marker: \n=== COMMIT:

## v0.2.1 — arachna init

- --init: interactive .arachna.json bootstrap
- --init --defaults: auto-detect code/tests/docs/git profiles

## v0.2.0 — Single file output, manifest, test reorg, 90% coverage

- Single file output: chat-code.md instead of chat-code_1.md
- Manifest (.arachna_manifest.json) for cleanup between runs
- 129 tests, 90% coverage

## v0.1.5 — Shebang detection

- formatter.py: detect language from shebang
- 107 tests, 66% coverage

## v0.1.4 — Tests, coverage, bugfixes

- 102 tests, 65% coverage
- gatherer.py: deduplicated with _collect_named_sections

## v0.1.3 — Validate, gitignore, default profile, runner tests

- validator.py: check split_mode, max_tokens, content source, split_marker
- gitignore.py: parse .gitignore patterns for auto-exclusion

## v0.1.2 — Dry-run, renderer, pre-commit, ruff

- gatherer.dry_run: real split simulation with per-section token tracking
- renderer: aligned output

## v0.1.1 — Tests + fixes

- 29 tests: tokenizer, splitter, config, formatter
- Fixed _split_to_sections: .strip() removed, preserves leading newlines

## v0.1.0 — MVP

- tokenizer, runner, formatter, splitter, gatherer, collector, config, CLI
- 4 split modes, exclude_patterns, _FILENAME_LANG
