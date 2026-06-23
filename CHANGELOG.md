# Changelog

## v5.2.2 — SonarCloud Security + Code Quality: 0 findings
- S2083/S8707: inline path validation in SafePath I/O methods + explicit validate_path before I/O
- S5332: urlparse-based URL validation, http only for local/private hosts via DNS
- S5852: all regex patterns refactored — greedy quantifiers with clear stop chars, no \s* inside groups
- S3516: validate_remote_url returns None (void), callers use url directly
- S5713: removed redundant urllib.error.URLError from except
- config/defaults.py: DEFAULT_PRESETS_URL, _COMMON_EXCLUDE_DIRS, DEFAULT_EXCLUDE
- config/urls.py: validate_remote_url with DNS-based local host check
- Removed duplicated formatting/__init__.py (86% dup with formatter.py)
- Removed unused ObjectStore/ContentFormatter Protocols from interfaces.py
- Removed unused re-exports from domain/execution/__init__.py
- Narrowed domain/__init__.py __all__ to public API only
- Fixed ARCHITECTURE.md api/config imports claim
- Quality Gate: 0 Security, 0 Reliability, 0 Maintainability issues

## v5.2.1 — SonarCloud + Audit fixes, test suite dedup, dead code removal
- SonarCloud: 0 findings (S1172 x3, S2083 x4, S8707, S5852 x3 — all fixed)
- Audit R1+R2: 25/25 findings fixed (2 HIGH, 5 MEDIUM, 7 LOW, 5 LEGACY, 6 code quality)
- HIGH: Removed dead config param from api/snapshot.py (S1172 x3)
- HIGH: Fixed broken import in examples/delirium_agent.py
- MEDIUM: ProfileConfig.from_dict() — 6 copies deduplicated into one classmethod
- MEDIUM: S5852 regex refactored: split 3 problematic patterns into 6 safe ones
- MEDIUM: atomic_write.py accepts SafePath — all 14 call sites updated
- MEDIUM: _check_toctou() returns resolved Path — eliminates S2083 in path_utils.py
- MEDIUM: store.py split json.loads one-liner for S2083
- MEDIUM: init.py _write_config passes SafePath directly — S8707 fixed
- MEDIUM: Shell features documented in SECURITY.md + 3 adversarial pre_commands tests
- MEDIUM: Deleted backward-compat re-exports: snapshot/snapshots.py, interfaces.py
- MEDIUM: get_root() — ArachnaConfig only, dict branch removed
- MEDIUM: Tokenizer Protocol type hints added across codebase
- MEDIUM: Global state replaced with @lru_cache factories (gatherer_strategies, tokenizer, presets)
- LOW: 6 bare except → specific exceptions
- LOW: Dead if __name__ block removed from config/completion.py
- LOW: merge_lock PID-based stale lock detection
- LEGACY: ArachnaConfig | dict removed from all CLI signatures
- LEGACY: Private symbols removed from config/core/ and snapshot/ __all__
- LEGACY: domain/__init__.py __all__ narrowed to public API only
- LEGACY: profiler.py fragile private import fixed
- Tests: 12 edge files merged, 6 coverage files renamed, 8 duplicates removed
- Tests: test_runner_edge.py (35 tests) merged into test_run_command.py
- Tests: gatherer_core.py (deprecated re-export) deleted, direct imports
- Tests: conftest.py optimized (make_popen_mock, tmp_workspace)
- Tests: all docstrings cleaned of version tags and BUG/TC prefixes
- Tests: 1644 passed, 3 skipped, 96% coverage

## v5.2.0 — Architecture: package reorganization + type safety
- domain/ split into 5 subpackages: cache/, collection/, formatting/, tokenization/, execution/
- snapshot/ split into 3 subpackages: store/, diff/, rename/
- config/ split into 3 subpackages: core/, presets/, setup/
- Dataclass config: ProfileConfig + ArachnaConfig replace dict-based access (~200 get() calls)
- Enum/Literal types: CollectionMode, OutputFormat, SplitMode for static checking
- Break api/ ↔ config/ cycle: api/ no longer imports from config/
- Move compute_diff_stats to domain/differ_stats.py (pure function, no snapshot dependency)
- SafeLogger: _sanitize_log() centralized in domain/runner.py
- time.sleep → os.utime in incremental tests (deterministic)
- mock_popen deduplicated to tests/conftest.py
- 1641 tests, 96% coverage, 0 bugs

## v5.1.1 — Security hardening + SonarCloud cleanup
- S2076: Block command substitution $() and backticks in pre_commands mode (CRITICAL)
- S5145: Sanitize CRLF in logger calls before logging (runner.py, snapshot_diff_commands.py)
- S2737: Remove unnecessary try-except from fallback lock_fn in collector.py
- S1481: Replace unused unlock_fn with _ in _merge_lock
- S7504: Replace list(old_files.keys()) with set(old_files) in snapshot_diff_files.py
- TOCTOU protection in SafePath I/O methods (resolve + is_relative_to double-check)
- SafePath.to_path() method — clean conversions without Path(str(...)) workarounds
- _version field in snapshot manifests with migration placeholder (store.py)
- Atomic output file writes via atomic_write_text in _write_parts and _write_diff_parts
- skip_clean parameter to deduplicate manifest cleanup in collect --all
- 1643 tests, 96% coverage, 0 SonarCloud findings (10 accepted as secure-by-design)

## v5.1.0 — SafePath + full audit resolution
- CRITICAL: Removed importlib.import_module fallback in tokenizer.py — unknown packages rejected
- HIGH: Renamed private functions to public in snapshot_diff (apply_repo_map_to_sections, collect_snapshot_content)
- SafePath: Path wrapper with mandatory root validation — eliminates all S2083/S8707 false positives
- MEDIUM: Decomposed formatter.py (605 lines → 6 sub-modules) and snapshot_diff.py (720 lines → 4 sub-modules + helpers)
- MEDIUM: Narrowed except Exception → specific types in atomic_write.py, cache.py, hook.py, snapshot_diff.py
- LOW: Atomic writes in init.py, presets.py, _helpers.py via atomic_write_text
- LOW: KeyError counted as error in validation, DANGEROUS log elevated to error
- LOW: _log_writer replaced with parameter injection, threading.Lock for all global state
- LOW: importlib.reload replaced with @lru_cache factory functions
- SonarCloud: S1481, S2737, S7504 fixed
- 1616 tests, 96% coverage, 0 SonarCloud findings

## v5.0.0 — Architecture cleanup
- BREAKING: watch/ package renamed to snapshot/ — public API import changed
- Deduplicated DiffSection: differ.py → api_types.py
- Cleaned docstrings, narrowed __all__, documented split dispatch
- SonarCloud fixes: S1481, S3776 x3, S5145, S8502, S7504
- 1611 tests, 95% coverage

## v4.2.1 — SonarCloud cleanup
- S3776: 14 functions reduced to cognitive complexity <=15
- S5843: _RE_ES6_IMPORT split into _RE_ES6_IMPORT_FROM + _RE_ES6_IMPORT_BARE
- S2083: validate_path in _write_parts, _write_diff_parts, clean_manifest, list_snapshots
- S8707: _validate_output_dir rejects path separators in init.py
- S2737: comment added to empty except in collector.py
- S1481: unused variable replaced with _
- 1613 tests, 95% coverage

## v4.2.0 — Code quality
- _CollectParams dataclass: 14 params → 1 object in _FullModeStrategy
- remote.py: domain/ → config/ (layer violation fix)
- _BLOCK_PATTERNS: named groups (?P<name>...) → numbered (...), m.group("name") → m.group(1)
- math.isclose() for floating point comparisons in rename detection
- compressor.py: _RE_TRAILING_WS regex → str.rstrip(), re import removed
- _RE_C_LIKE_IMPORT → _RE_C_LIKE_IMPORT_CHAIN (5 single-purpose patterns)
- gatherer_core.py → gatherer_files.py + gatherer_commands.py
- watcher.py → watcher_diff.py + watcher_rename.py
- presets.py → presets_remote.py (fetch_presets + merge_presets)
- path_utils.py: validate_path() for SonarCloud S2083 path injection
- Cognitive complexity reduced: all 35+ C-functions → B
- diff --line-numbers: line numbers in REMOVED/ADDED blocks
- 1607 tests, 95% coverage, 0 bugs

## v4.1.1 — Quick fixes from audit
- 17 code smells fixed: unused params, deduplicated literals, empty blocks
- completion.py: argparse subparsers for bash/zsh
- is_excluded: support directory-scoped patterns
- remote: true profile field + strict --profile for --repo
- fmt restored in diff chain for XML output
- _find_query_candidate accepts root parameter
- 1571 tests, 95% coverage

## v4.1.0 — Quality of life
- max_tokens: -1 as unlimited (0 rejected, follows Unix convention)
- line_numbers profile field: prepend 5-digit line numbers to file sections
- arachna collect --repo <url>: clone, auto-detect, collect, cleanup
- conftest.py deduplication: make_config/setup_config/make_profile from 6 files -> 1 root
- runner.py: 96% -> 99% coverage (except Exception -> except OSError)
- differ.py: 99% -> 100% coverage (dead code removed)
- 1556 tests, 95% coverage

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
- BUG-001: profile files resolved relative to project root
- BUG-002: unknown extensions checked for null bytes before skipping as binary
- 1511 tests, 95% coverage

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
