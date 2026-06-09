# Changelog

## v3.2.0 — Benchmarking + Oversized sections + Profile

- arachna profile command: measure token savings across all modes on real project
- Benchmark overhaul: memory (RSS), baseline tracking, warm-up, throughput, stress tests (50K files)
- Structural diff benchmarks: Python AST vs JS tree-sitter comparison
- Oversized sections fix: split_sections with paragraph->line->character fallback chain
- Continuation markers (CONTINUES/CONTINUED) and [split across N parts] in TOC
- BUG-001 closed: oversized sections no longer truncated
- Business model section in README
- 1251 tests, 92% coverage, 0 bugs

## v3.1.0 — Plugin system

- Plugin system: environment detector (pipx, poetry, uv, conda, venv, system, PEP 668)
- Plugin: tree-sitter structural diff for JavaScript, TypeScript, Go
- Plugin: tiktoken/transformers token counting
- pyproject.toml: per-language extras (arachna[javascript], arachna[go], etc.)
- arachna plugins list/install/uninstall commands
- Lazy import with fallback to text diff for uninstalled plugins
- requirements-dev.txt: tree-sitter, tiktoken, transformers for local development
- 1233 tests, 92% coverage, 0 bugs

## v3.0.0 — CLI redesign with argparse subparsers

- BREAKING: Flat --flag CLI replaced with hierarchical subcommands
- `arachna --profile code` → `arachna collect --profile code`
- `arachna --all` → `arachna collect --all`
- `arachna --snapshot create` → `arachna snapshot create`
- `arachna --diff --from X` → `arachna diff --from X`
- `arachna --store stats` → `arachna store stats`
- `arachna --presets-update` → `arachna presets update`
- `arachna --completion bash` → `arachna completion bash`
- `arachna --doctor` → `arachna doctor`
- `arachna --init` → `arachna init`
- Remove cli_watch.py — all handlers in __main__.py
- Remove all manual sys.argv parsing
- Plugin stubs (list/install/uninstall) for v3.1
- 1188 tests, 92% coverage, 0 bugs

## v2.9.2 — Zero-dep fixes + Streaming pipeline

- Fix: Streaming pipeline for full mode — O(max_tokens) memory, pre_commands + query + compress work
- Fix: TOC substring matching — split_sections returns indices, no more content.strip() in part_content
- Fix: Config inheritance — "extends" field with typed merge (scalars override, exclude append, sources replace)
- Fix: Config inheritance UX — warnings on field conflicts between parent and child
- Fix: collect_api double I/O — parts from memory, write_to_disk=False for agent API
- Fix: Snapshot paths — relative to project root, portable across Windows/Linux
- Fix: Sandbox max_output_size — Popen with chunked read, ARACHNA_MAX_OUTPUT_SIZE env var
- Fix: chars_per_token in profile — ARACHNA_CHARS_PER_TOKEN env var, per-profile override
- Fix: run_command always returns str with truncation marker, no tuple
- Fix: All internal callers updated for collect() 3-tuple return
- Doc: Known limitations section in README
- Doc: ARCHITECTURE.md with streaming data flow
- Doc: BENCHMARKS.md with real numbers for all modes
- 1121 tests, 92% coverage, 0 bugs

## v2.9.1 — Architecture + Code Quality fixes

- MEDIUM ARCH-01: Strip strings/comments before brace matching in _extract_braced_block
- LOW CQ-02: _collect_import_graph extracts deps from section content with _generate_header fallback
- LOW CQ-04: _detect_renames_and_moves limits similarity check to files < 1MB
- LOW CQ-06: split_sections truncates oversized sections like _handle_single
- LOW CQ-07: _format_added accepts tokenizer param, uses binary search for accurate truncation
- LOW CQ-08: cache.py get_changed_files documents cache mutation in docstring
- LOW CQ-09: _parse_python_blocks returns None on SyntaxError for fallback to text diff
- LOW CQ-10: store.py create_snapshot docstring documents non-atomic tradeoff
- LOW CQ-11: gitignore.py docstring documents implementation limitations
- LOW CQ-12: collector.py adds O_CREAT|O_EXCL fallback for merge lock
- LOW CQ-13: splitter.py binary search adds max iterations guard
- LOW CQ-14: init.py catches EOFError in _ask/_ask_yes, returns default
- LOW CQ-15: presets.py fetch_presets uses ARACHNA_PRESETS_TIMEOUT env var
- 1071 tests, 92% coverage, 0 bugs

## v2.9.0 — Security hardening

- HIGH SEC-01: Two-level command allowlist — restricted mode (11 commands, no shell) for internal calls, pre_commands mode (extended allowlist, shell=True) for user config
- HIGH SEC-02: Shell redirection blocked in restricted mode, allowed in pre_commands — user controls .arachna.json
- HIGH SEC-03: Path traversal protection — validate_snapshot_id() with regex ^[\w][\w.-]*$ across all store operations
- HIGH SEC-04: Tokenizer top-level statement validation — only FunctionDef/ClassDef/Import allowed, no Call/Expr at top level
- MEDIUM SEC-05: URL scheme validation in --presets-update — only http:// and https:// allowed
- MEDIUM ARCH-02: TOC section indices from split_sections instead of content matching
- LOW CQ-01: Pre-generated header passed to _apply_repo_map_to_section to avoid double ast.parse
- LOW CQ-03: Reject patterns containing ".." with warning
- LOW CQ-05: Atomic write_object via tempfile.mkstemp + os.replace
- Fix: all pre_commands/command calls use allow_file_args=True
- 1071 tests, 92% coverage, 0 bugs

## v2.8.2 — Design/UX + Final polish

- --no-pre-commands CLI flag to skip pre_commands for quick collection
- --mode headers help text clarified
- _SAFE_TOKENIZERS configurable via ARACHNA_SAFE_TOKENIZERS env var
- _EXT_LANG: add .hpp, .cmake, .gradle, .lock, .conf
- ARACHNA_PRE_COMMAND_DELAY for rate limiting between pre_commands
- Warn when pre_command/command produces no output in snapshot
- _load_builtin_presets: mtime-based cache invalidation
- store.py: atomic write for .arachna/.gitignore (race condition fix)
- Cross-snapshot pre_commands diff: show removed lines with - prefix
- Multi-part diff summary header with change counts per part
- 1043 tests, 93% coverage, 0 bugs

## v2.8.1 — Code Quality + Testability

- LOW: Decompose watcher.compute_diff — extract _diff_files_sections, _diff_pre_commands_sections, _diff_command_section
- LOW: Unify _cmd_clean glob patterns — single loop for all chat-* formats
- LOW: _RE_C_LIKE_BLOCK refactor — 15 named groups (?P<name>...) instead of fragile heuristic
- LOW: _should_skip_binary refactor — decision table with explicit branches
- LOW: Replace os.path.basename with pathlib in _diff_pre_commands_structural
- LOW: _write_parts TOC — use section indices instead of content.strip() matching
- LOW: split_sections — add was_truncated warning via logger
- LOW: _filter_by_query — filter pre_commands by default, add include_pre_commands param
- LOW: _detect_renames_and_moves O(N²) — limit similarity comparison to same-extension
- LOW: _format_added — subtract truncation message length from token limit
- LOW: _run_profile — use _ProfileResult dataclass instead of tuple
- LOW: _read_file_from_store — build {path: hash_spec} dict once, O(1) lookup
- LOW: _cmd_snapshot info — use list_snapshots result directly, avoid double manifest load
- LOW: gatherer — warn when both command and directories present
- LOW: runner._log_command — injectable _write_log for testability
- LOW: _store_root — accept explicit root path parameter
- 1025 tests, 93% coverage, 0 bugs

## v2.8.0 — Security + Architecture core

- HIGH: Log injection fix — sanitize \n and \r in audit log
- HIGH: Remove find, env, hg, svn from _ALLOWED_COMMANDS, add find to _BLOCKED_WORDS
- MEDIUM: C_LIKE_LANGS and SCRIPT_LANGS as public constants — single source of truth in formatter.py
- MEDIUM: Unify three repo-map implementations — _apply_repo_map_to_sections in gatherer.py
- MEDIUM: Remove duplicate language sets, _parse_blocks, and repo-map helpers from watch.py
- MEDIUM: Fix tokenizer passthrough in _cmd_diff → _write_diff_parts
- MEDIUM: Extract _format_file_list — DRY _format_scanned_files and _collect_specific_files
- MEDIUM: Extract _parse_output_dir helper in cli_watch.py
- MEDIUM: Extract _collect_referenced_hashes shared by stats() and gc()
- MEDIUM: @lru_cache on load_config with conftest cache_clear fixture
- 1025 tests, 93% coverage, 0 bugs

## v2.7.0 — LOW fixes, store, packaging, polish

- LOW-01: limit _get_audit_log_path traversal to 5 parent levels
- LOW-02: skip symlinked directories in gitignore and gatherer
- LOW-05: O(1) truncation for default tokenizer in _handle_single
- LOW-06: fix _split_to_sections marker prefix on first element
- LOW-07: store.gc removes empty subdirectories in objects/
- LOW-08: _hash_path mkdir only on write, not read
- LOW-09: better error message for corrupted/non-zlib objects
- LOW-10: explicit cache cleanup for deleted files in incremental mode
- LOW-12: _should_skip_binary detects no-extension binaries via null bytes
- LOW-13: multi-line import regex fallback for Python SyntaxError
- LOW-15: _cmd_presets_update aborts on corrupted local presets.json
- LOW-16: init.run_defaults warns when no profiles detected
- LOW-17: _MAX_HASH_SIZE configurable via ARACHNA_MAX_HASH_SIZE env var
- LOW-22: [project.optional-dependencies] added to pyproject.toml
- LOW-23: license field updated to PEP 639 (license-files)
- LOW-24: CHANGELOG descriptions for v0.1.4 and v0.1.5
- LOW-25: KeyError guard for get_profile in _cmd_validate
- LOW-26: _load_all_manifests shared by stats() and gc()
- MEDIUM-01: warn when neither fcntl nor msvcrt available for merge lock
- 998 tests, 1 skipped, 0 failures

## v2.6.0 — Code quality, formatter, differ, test coverage

- MEDIUM-03: Extract _apply_repo_map_to_section (DRY repo-map logic)
- MEDIUM-04: _assemble_command_content accepts query/mode for API symmetry
- MEDIUM-05: _assemble_file_content split into pipeline stages (collect → filter → compress → split)
- MEDIUM-11: _format_added truncates oversized added files with token limit warning
- MEDIUM-12: _RE_PY_IMPORT handles multiple imports on one line (import a, b)
- MEDIUM-13: Add .tsx and .jsx to _EXT_LANG
- MEDIUM-14: PHP use-statements in _RE_C_LIKE_IMPORT
- MEDIUM-15: Go type block name captures first identifier after type, not struct/interface keyword
- MEDIUM-17: _build_toc uses section indices instead of content matching (compression-safe)
- MEDIUM-19: watch.py coverage raised from 90% to 93%+
- MEDIUM-20: collector.py coverage raised from 87% to 90%+
- LOW-18: Property-based tests for tokenizer, compressor, splitter (hypothesis)
- LOW-19: Mock msvcrt merge_lock on Unix
- LOW-20: UTF-16 presets.json error handling test
- LOW-21: Unicode edge cases (emoji sequences, combining chars, RTL)
- Lazy loading: @lru_cache on _load_builtin_presets (merged dict no longer cached)
- hypothesis added to requirements-dev.txt
- 998 tests, 1 skipped, 0 failures

## v2.5.0 — Security, architecture, watcher fixes

- HIGH-01: XML escaping in differ.py (xml.sax.saxutils.escape)
- HIGH-02: Static import analysis for local tokenizer files (ast.parse)
- HIGH-03: Watch CLI extracted from __main__.py into cli_watch.py (~470 lines)
- HIGH-04: collect() accepts name_template parameter — _cmd_diff_all clean
- MEDIUM-02: --diff --all and --from together now produce error
- MEDIUM-06: watcher._apply_repo_map_diff logs fallback to text diff
- MEDIUM-07: _normalize_path collapses double slashes
- MEDIUM-08: _path_matches_profile normalizes paths with os.path.normpath
- MEDIUM-09: _collect_snapshot_content skips files outside cwd with warning
- MEDIUM-10: _diff_pre_commands_line uses difflib.SequenceMatcher (preserves order)
- LOW-14: os.path.basename for tree detection in pre_commands diff
- MEDIUM-18: Restored informative warning messages in presets.py
- BUG-001: validate --profile and --name values don't start with -
- docs/LLM_INTEGRATION.md: LLM agent workflow guide
- 970 tests, 93% coverage

## v2.4.0 — Quality improvements

- presets.py: fetch_presets(url) — download presets from remote URL
- presets.py: merge_presets(builtin, remote, local) — three-way merge, local wins
- __main__.py: --presets-update command with --url override
- __main__.py: --diff --all for full project as diff (no snapshot needed)
- --diff --all --mode repo-map/headers/structural support
- --diff --all --query filtering and --compress support
- tests/collector/test_merge_lock.py: fcntl + msvcrt (Windows) lock tests
- 907 tests, 92% coverage

## v2.3.0 — Watch improvements

- Structural diff for pre_commands: line diff for tree/git tag, marker diff for git log
- Repo-map diff reads full source from store, compares blocks with body hashes
- BUG-001: tree command structural diff fixed
- BUG-002: --diff --mode repo-map reads full source (not diff snippets)
- 879 tests, 92% coverage

## v2.2.0 — Language presets expansion

- 7 new presets: Go, Rust, Zig, Lua, Elixir, Haskell, Gleam (24 total)
- formatter.py: add zig, lua, elixir, haskell, gleam to _EXT_LANG and _C_LIKE_LANGS
- 17 new tests: detect + preset_to_profile for each language + extensions
- 833 tests, 92% coverage

## v2.1.0 — Documentation & examples

- docs/TUTORIAL.md: full Agent API tutorial with 8 code examples
- examples/delirium_agent.py: Delirium agent integration example
- arachna.1: man page with all commands and options
- README.md: Programmatic API section, collection modes, structural diff
- Makefile: trailing-ws and fix-trailing-ws targets
- pre-commit: trailing-ws hook
- Comprehensive docstrings across all public API modules

## v2.0.0 — Agent API + structural diff

- watch.py: public API for snapshots, diffs, store (create/list/update/delete/info/compute_diff/stats/gc)
- collect_api.py: programmatic collection with query/mode support
- api_types.py: SnapshotInfo, DiffStats, DiffSection, DiffResult, CollectResult, StoreStats, GCResult
- api_errors.py: ArachnaError, SnapshotNotFoundError, SnapshotExistsError, ProfileNotFoundError
- differ_structural.py: structural diff for Python (ast), C-like/script (regex), fallback difflib
- --mode structural for --diff CLI
- Repo-map fix: extract_signatures applied to raw text before markdown formatting
- 816 tests, 92% coverage

## v1.8.0 — Headers, --query, repo-map mode

- formatter.py: _generate_header extracts imports/exports (Python: ast, C-like: regex, Ruby/Elixir/Lua: regex)
- splitter.py: extract_signatures for repo-map mode (Python: ast, C-like/script: regex)
- gatherer.py: _filter_by_query with keyword scoring + import chain (depth 2)
- gatherer.py: _collect_import_graph from header deps
- __main__.py: --query and --mode (full/headers/repo-map) flags
- 24 new tests: headers (8), query (8), extract_signatures (8)
- 755 tests, 92% coverage

## v1.7.1 — Watch fixes: diff file naming, unified part numbering

- _write_parts: always use numbered filenames (name_1.md, name_2.md)
- _write_diff_parts: include snapshot name in filename (chat-diff-{snapshot}_N.md)
- _cmd_diff: cross-snapshot naming (chat-diff-{from}-to-{to}_N.md)
- _cmd_clean: update glob patterns for new filenames
- runner.py coverage: 83% → 89%, __main__.py: 89% → 90%
- 731 tests, 92% coverage

## v1.7.0 — Watch Advanced

- --diff --to: cross-snapshot diff between two snapshots
- Rename detection: exact (same hash) and similar (SequenceMatcher > 0.7)
- Move detection: same hash, different directory
- Grouped diff output: renamed, moved, modified, added, deleted
- Summary header with counts
- --snapshot info <id>: detailed snapshot info
- --snapshot info <id> --profile/--stats: profile or stats only
- --snapshot rename <old> <new>: rename snapshot
- --snapshot list: removed duplicate id/name column
- --diff --flat: flat output for backward compatibility
- store.py: rename_snapshot method
- differ.py: similarity field, renamed/moved counts in stats
- 36 new tests

## v1.6.5 — README update for Watch CLI

- README.md: updated all Watch commands to v1.6.4 syntax

## v1.6.4 — Watch CLI redesign

- --snapshot: explicit subcommands (list, create, update, delete)
- --snapshot create: --name required, duplicate names raise SnapshotExistsError
- --snapshot update: re-scan and update existing snapshot
- --diff: writes to chat-diff_N.md files instead of stdout
- --diff: auto-selects single snapshot, hints for multiple
- --diff --stat: show stats only (modified/added/deleted counts)
- --diff: profile from manifest if --profile not specified
- store.py: manifest stores full profile dict, update_snapshot added
- store_errors.py: SnapshotExistsError added
- collector.py: _write_diff_parts for token-split diff output
- Removed --full flag (_cmd_diff_full, _combine_full_and_diff)
- 654 tests, 92% coverage

## v1.6.3 — Watch: command-based profiles support

- watcher.py: create_snapshot executes pre_commands and command, stores output in manifest
- watcher.py: compute_diff diffs pre_commands and command output against snapshot
- store.py: create_snapshot accepts optional pre_commands/command dicts
- store.py: gc() and stats() scan pre_commands/command hashes
- 9 new tests: command profiles, pre_commands, backward compat, edge cases

## v1.6.2 — Watch polish: profile files + --diff --full

- watcher.py: create_snapshot and compute_diff include profile files (not just directories)
- watcher.py: _read_profile_files helper for explicit file reading with error handling
- watcher.py: _path_matches_profile checks explicit files list
- __main__.py: _cmd_diff supports --full flag for combined full context + diff
- __main__.py: _cmd_diff_full orchestrates collect + diff + combine into single output
- __main__.py: _combine_full_and_diff merges context and diff sections
- __main__.py: _cmd_clean handles chat-diff-full files
- 619 tests, 92% coverage

## v1.6.1 — Watch MVP + README fix

- README.md: fix malformed code blocks in PyPI description
- All v1.6.0 features included (snapshots, diffs, store)

## v1.6.0 — Watch MVP

- store.py: content-addressable store with SHA256 + zlib compression
- store.py: create/load/list/delete snapshots, HEAD tracking
- store.py: gc() garbage collection, stats() with dedup %
- store_errors.py: CorruptedStoreError, ObjectNotFoundError
- differ.py: LLM-optimized diff with markdown and XML formats
- differ.py: DiffSection dataclass, compute_diff_stats
- watcher.py: create_snapshot + compute_diff orchestration
- watcher.py: _path_matches_profile for profile change detection
- CLI: --snapshot create/list/delete, --diff, --store gc/stats
- 606 tests, 93% coverage

## v1.5.3 — Smart hybrid incremental cache

- cache.py: v2 format with mtime_ns + size + SHA256
- cache.py: fast path — size + mtime_ns within 1ms tolerance skips file
- cache.py: SHA256 fallback detects false positives (git checkout)
- cache.py: automatic migration from v1 format
- ci: add PyPI publish job on version tags
- 530 tests, 92% coverage

## v1.5.2 — Race condition fix + escaped pipes

- collector.py: add file locking (_merge_lock) for concurrent merge safety
- runner.py: handle escaped pipes (\|) in _split_pipe_parts
- runner.py: handle backslash escaping in double-quoted strings per shell rules

## v1.5.1 — LOW fixes from audit

- gatherer.py: make tokenizer required parameter in _collect_named_sections
- __main__.py: direct if-elif dispatch in main()
- completion.py: static completion, no dynamic profile listing
- presets: remove unused service field from all 17 JSON files
- formatter.py: _TEXT_EXTENSIONS generated from _EXT_LANG
- tests/cache: absolute paths, no monkeypatch.chdir
- tests/collector: fix fragile mock target in test_post_commands_executed
- 478 tests, 94% coverage

## v1.5.0 — Architecture refactor + LOW fixes

- presets.py: split PRESETS dict into individual JSON files
- presets.py: remove _SERVICE_PRESETS hardcoded set
- collector.py: decompose collect() into _write_parts() and _run_post_commands()
- splitter.py: remove CHARS_PER_TOKEN dead code
- __main__.py: remove unreachable return after sys.exit
- formatter.py: add _TEXT_EXTENSIONS, single _should_skip_binary() entry
- 475 tests, 94% coverage

## v1.4.4 — Security allowlist cleanup

- runner.py: remove mkdir, xargs, sed, awk, tee from _ALLOWED_COMMANDS
- All commands now strictly read-only
- 455 tests, 94% coverage

## v1.4.3 — Unreal Engine preset + AGPLv3

- presets.py: add Unreal Engine preset
- LICENSE: switch from MIT to GNU AGPLv3
- 449 tests, 94% coverage

## v1.4.2 — Audit LOW fixes + compression stats bug

- gatherer.py: fix compression stats
- runner.py: remove touch from _ALLOWED_COMMANDS
- __main__.py: extract _print_collected, pass tokens_by_file from memory
- hook.py: remove S_IXOTH from chmod
- tokenizer.py: document safety check order
- collector.py: collect() returns tuple (files, tokens_by_file)

## v1.4.1 — Unified split + audit fixes

- gatherer.py: unified split, removed pre_split_mode/pre_split_marker
- splitter.py: split_sections() for pre-built section lists
- 436 tests, 93% coverage

## v1.4.0 — Security hardening + cleanup

- tokenizer.py: deny by default, remove fallback to sys.modules
- runner.py: remove chmod, chown from _ALLOWED_COMMANDS
- gatherer.py: skip symlinks, decompose _assemble_content
- 414 tests, 93% coverage

## v1.3.0 — Multi-source split modes + bug fixes

- gatherer.py: pre_split_mode and pre_split_marker
- runner.py: quote-aware pipe splitting, word-boundary matching (BUG-001)
- presets.py: c_cpp detect reduced to CMakeLists.txt only (BUG-004)

## v1.2.2 — CLI consistency

- init.py: run_interactive filters autodetection by --preset

## v1.2.1 — Security fix

- tokenizer.py: _is_safe_tokenizer with whitelist and stdlib blocking
- presets.py: tokenizer validation in load_presets_from_file

## v1.2.0 — Presets as config

- presets.py: load_presets_from_file for external presets.json

## v1.1.0 — Language & engine presets

- presets.py: 16 presets, detect_presets(), preset_to_profile()

## v1.0.2 — Fix --version CLI

- __main__.py: handle --version before argparse

## v1.0.1 — Windows test fixes

- tests: cross-platform stability

## v1.0.0 — Public release

- First public release on PyPI

## v0.9.5 — GitHub prep

- pyproject.toml: URLs, README badges

## v0.9.4 — Final polish

- runner.py: import json to module level
- gatherer.py: _assemble_content shared pipeline

## v0.9.3 — Final fixes

- __main__.py: _cmd_validate uses get_profile()
- tests/runner: CompletedProcess instead of MagicMock

## v0.9.2 — Pre-release fixes

- hook.py: is_dir() check
- gitignore.py: ValueError handling from relative_to

## v0.9.1 — Version sync

- __init__.py + pyproject.toml sync

## v0.9.0 — Infrastructure

- PyPI packaging, GitHub Actions CI

## v0.8.5 — Sandbox

- runner.py: dry-run + interactive confirmation

## v0.8.4 — Merge

- collector.py: --merge flag, _find_next_part_num

## v0.8.3 — Git hooks

- hook.py: arachna --install-hook

## v0.8.2 — Doctor

- doctor.py: arachna --doctor

## v0.8.1 — Low fixes

- config.py: DEFAULT_EXCLUDE from _COMMON_EXCLUDE_DIRS
- splitter.py: tokenizer-based truncation

## v0.8.0 — God function

- gatherer.py: decompose _collect_named_sections

## v0.7.5 — Truncation API + shlex

- splitter.py: logger.warning for was_truncated
- runner.py: shlex ValueError handling

## v0.7.4 — Sandbox pipe fix

- runner.py: validate each pipe part individually

## v0.7.3 — Test stability

- tests: tmp_path/monkeypatch, mock subprocess

## v0.7.2 — Architecture cleanup

- gatherer.py: remove global _TOKENIZE
- collector.py: atomic manifest writes
- splitter.py: CHARS_PER_TOKEN constant

## v0.7.1 — Critical fixes

- runner.py: remove interpreters from _ALLOWED_COMMANDS
- splitter.py: tokenizer passthrough fix

## v0.7.0 — Security sandbox, architecture cleanup

- runner.py: sandbox validation, audit log
- cache.py: atomic writes

## v0.6.0 — Pluggable tokenizer

- tokenizer.py: load_tokenizer(spec)

## v0.5.0 — Tests, safety, audit fixes

- 175 tests, 90% coverage

## v0.4.2 — Audit fixes

- gatherer.py: remove dead code
- CJK token tests fixed

## v0.4.1 — Table of contents + manifest

- TOC in each part, chat-manifest.md

## v0.4.0 — Shell completion + hooks

- completion.py: bash and zsh
- post_commands support

## v0.3.0 — Compress, incremental, formats, binary

- --compress, --incremental, --format, include_binary

## v0.2.2 — Git split marker, per-profile manifest cleanup

- git split_marker fix, --all/--profile cleanup

## v0.2.1 — arachna init

- --init interactive + --defaults

## v0.2.0 — Single file output, manifest, test reorg

- chat-code.md, manifest, 129 tests, 90% coverage

## v0.1.5 — Shebang detection

- formatter.py: detect language from shebang (#!python3, #!/bin/bash, etc.)
- Supports: python, bash, node, ruby, perl
- 5 new tests, 107 total, 66% coverage

## v0.1.4 — Tests, coverage, bugfixes

- 102 tests (up from 46), 65% coverage (up from 25%)
- gatherer.py: deduplicated with _collect_named_sections, 92% coverage
- renderer.py: 100% coverage
- formatter.py: binary file detection (null bytes)
- gitignore.py: skip venv/.gitignore and hidden dirs

## v0.1.3 — Validate, gitignore, default profile, runner tests

- validator.py: check split_mode, max_tokens, content source, split_marker
- gitignore.py: parse .gitignore patterns for auto-exclusion
- Default profile when .arachna.json has no profiles
- CLI: --validate flag, exit code 1 on errors
- test_validator.py: 10 tests
- test_runner.py: 7 tests

## v0.1.2 — Dry-run, renderer, pre-commit, ruff

- gatherer.dry_run: real split simulation with token tracking
- renderer: aligned output with section/part separators
- --dry-run, --output-dir, --verbose CLI flags
- Makefile: test, test-cov, lint, format, clean
- pre-commit: ruff + unit tests
- ruff config in pyproject.toml

## v0.1.1 — Tests + fixes

- 29 tests: tokenizer, splitter, config, formatter
- Fixed _split_to_sections: .strip() removed, preserves leading newlines

## v0.1.0 — MVP

- tokenizer, runner, formatter, splitter, gatherer, collector, config, CLI
- 4 split modes, exclude_patterns, _FILENAME_LANG
- shlex.split() for safe command execution
