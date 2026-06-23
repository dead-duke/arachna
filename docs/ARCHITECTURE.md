# arachna — Architecture

## Overview

arachna is a context layer for AI workflows: snapshots, diffs, profiles. Collect once, diff forever.

## Package structure (v5.3.0)

src/arachna/
  __init__.py           Version + public API re-exports
  __main__.py           CLI entry point: build_argparse() + main() dispatch

  domain/               Pure data transformations, no I/O dependencies
    __init__.py         Re-exports public API only
    api_types.py        Public API dataclasses (DiffSection, DiffStats, etc.)
    atomic_write.py     Atomic file writes (mkstemp + os.replace), SafePath-native
    compressor.py       Safe whitespace compression (str.rstrip, no regex)
    differ_stats.py     compute_diff_stats — pure function on DiffSection
    interfaces.py       Protocol definitions: Tokenizer
    path_utils.py       Path validation (validate_path) + SafePath class with TOCTOU protection

    cache/
      __init__.py
      cache.py          Smart hybrid incremental cache (mtime_ns + size + SHA256)

    collection/
      __init__.py
      collector.py      Orchestrator: gather -> split -> write -> post_commands
      gatherer.py       Facade over gatherer_files + gatherer_commands + gatherer_pre_commands + gatherer_query + gatherer_strategies
      gatherer_files.py Directory scanning, file formatting, exclude patterns
      gatherer_commands.py  Command execution: gather_files, gather_command
      gatherer_pre_commands.py  Pre_commands execution (extracted to break cyclic import)
      gatherer_query.py Query pipeline: import graph, scoring, filtering
      gatherer_strategies.py  Strategy pattern: FullModeStrategy with _CollectParams dataclass

    formatting/
      __init__.py
      formatter.py      Re-exports from all format_* sub-modules (backward-compatible)
      format_binary.py  Binary file detection and base64 formatting
      format_exclude.py fnmatch exclusion matching with directory support
      format_headers.py Deps/exports extraction for all languages (regex + AST)
      format_language.py Language detection, C_LIKE_LANGS, SCRIPT_LANGS, _EXT_LANG
      format_output.py  File section formatting (markdown/xml/json), SafePath integration
      format_parsers.py Parser functions (extracted to break cyclic import)
      format_sigs.py    Signature formatting for repo-map mode

    tokenization/
      __init__.py
      tokenizer.py      Token estimation, pluggable tokenizers, safety validation
      language_dispatch.py  HEADER_PARSERS + BLOCK_PARSERS mappings, regex timeout

    execution/
      __init__.py
      runner.py         Popen-based command execution, dual-mode allowlist, decomposed helpers
      splitter.py       Token-based splitting, oversized section fallback, pack_into_parts
      gitignore.py      .gitignore parser for auto-exclusion

  config/               Configuration, presets, init, validation
    __init__.py         VALID_SPLIT_MODES, COLLECTION_MODES, CollectionMode/OutputFormat/SplitMode Literal types
    completion.py       Bash and zsh shell completion (argparse subparsers)
    doctor.py           Full diagnostic: run_doctor(project_root, config)
    profiler.py         Benchmark runner: measures token savings across modes
    remote.py           Remote repository collection (git clone + collect)
    profile_config.py   ProfileConfig.from_dict() + ArachnaConfig dataclasses
    defaults.py         DEFAULT_PRESETS_URL, _COMMON_EXCLUDE_DIRS, DEFAULT_EXCLUDE
    urls.py             URL validation with DNS-based local host check

    core/
      __init__.py
      config.py         .arachna.json loader, profile resolution with extends
      validator.py      Profile validation

    presets/
      __init__.py
      presets.py        Language/engine presets, auto-detection, validation, @lru_cache
      presets_remote.py Remote presets: fetch_presets + merge_presets

    setup/
      __init__.py
      init.py           Interactive .arachna.json bootstrap, SafePath-native
      hook.py           Git post-commit hook installer

  snapshot/             Snapshots, diff, store, benchmarks
    __init__.py         Re-exports public API only
    benchmarks.py       Plugin benchmarks (structural-diff, tiktoken)

    store/
      __init__.py
      store.py          Content-addressable store (SHA256 + zlib, dedup, GC), manifest versioning
      store_errors.py   Store subsystem exceptions

    diff/
      __init__.py
      differ.py         LLM-optimized text diff (markdown + XML), line numbers
      differ_structural.py  Structural diff: Python AST, C-like regex, tree-sitter plugin
      snapshot_diff.py  Diff computation — orchestration + grouping
      snapshot_diff_helpers.py  Path normalization (_rel_path, _normalize_path)
      snapshot_diff_files.py    File collection, diff sections, path matching, store I/O
      snapshot_diff_commands.py Pre_commands/command execution and diff strategies, CRLF sanitization
      snapshot_diff_repo_map.py Repo-map transformation for diff sections

    rename/
      __init__.py
      snapshot_rename.py  Rename/move detection: exact hash + similarity matching

  plugins/              Optional dependency management
    plugins.py          Plugin system: environment detector, install/uninstall/list

  api/                  Stable public API for external consumers
    api_errors.py       Public API exception classes
    collect_api.py      Public Collection API (programmatic use)
    snapshot.py         Public Snapshot API (programmatic use)

  cli/                  CLI command handlers
    __init__.py         COMMAND_HANDLERS registry, @register decorator
    _helpers.py         Shared helpers: get_root, parse_output_dir, print_collected, etc.
    collect.py          collect --profile, --all, --repo, --list, --validate, --clean handlers
    snapshot.py         snapshot create/list/update/delete/info/rename handlers
    diff.py             diff --from, --to, --all, --line-numbers handlers
    store.py            store stats, store gc handlers
    plugins.py          plugins list/install/uninstall handlers
    presets.py          presets update handler
    doctor.py           doctor handler
    init.py             init handler + _dispatch_init for --install-hook
    completion.py       completion bash/zsh handler
    profile.py          profile (benchmark) handler
    manifest.py         manifest --json handler
    renderer.py         Dry-run output formatting

  presets/              Built-in preset JSON files (24 presets)

## Dependency flow

CLI handlers import from domain/, snapshot/, plugins/, api/, config/.
API layer imports from domain/ and snapshot/, plus types from config/ (ProfileConfig, CollectionMode, OutputFormat).
Snapshot layer imports from domain/.
Config layer imports from domain/.
Domain layer imports only from stdlib and other domain/ modules.

No circular dependencies. Internal imports at module level. Only plugin lazy imports remain (tiktoken, transformers, tree-sitter).

## Key architectural decisions

### v5.3.0: Audit resolution — 20 findings closed
- **Exception narrowing:** atomic_write.py, differ_structural.py, language_dispatch.py — broad except Exception replaced with specific types.
- **Splitter unification:** _handle_oversized_in_build removed. Command mode oversized sections split with CONTINUES/CONTINUED markers — same behaviour as file mode.
- **ProfileConfig migration:** 7 functions migrated from dict to ProfileConfig. _collect_pre_commands extracted to gatherer_pre_commands.py to break cyclic import.
- **Cyclic imports broken:** gatherer_pre_commands.py (gatherer_commands ↔ gatherer_files), format_parsers.py (format_headers ↔ language_dispatch). All internal imports lifted to module level.
- **Collector dead code:** isinstance(profile, ProfileConfig) checks removed — all callers pass ProfileConfig.
- **root: Path mandatory:** Every function that needs project root accepts explicit root parameter. Path.cwd() only in main() and _validate_preset_tokenizer.
- **_read_file_from_disk:** bare Path fallback removed, SafePath only.
- **__all__ cleanup:** domain/__init__.py, collection/__init__.py, snapshot/diff/__init__.py — private symbols removed.
- **print() → logger:** gatherer_files.py, gatherer_strategies.py — warnings migrated to logger.warning()/logger.info().
- **Compress stats:** _assemble_command_content now outputs compress statistics.
- **differ_structural:** threading.Lock replaced with @lru_cache on _check_plugins().
- **store.py:** explicit OSError warning on atomic_write_text fallback.
- **SafePath in tokenizer.py:** I/O operations wrapped in SafePath.
- 1660 tests, 96% coverage, 0 bugs.

### v5.2.2: SonarCloud + Audit fixes
- **S2083 path_utils:** _check_toctou() returns SafePath, I/O methods use typed SafePath — closes S2083 in path_utils.py.
- **S2083 atomic_write:** Fallback path.write_text()/write_bytes() on SafePath — closes S2083 in atomic_write.py.
- **S2083 store.py:** Explicit SafePath type annotations on local variables in rename_snapshot — closes S2083 in store.py.
- **S8707 init.py:** _validate_output_dir returns str, used inline in SafePath constructor — closes S8707 in init.py.
- **S8707 atomic_write:** Fallback on SafePath instead of bare Path — closes S8707 in atomic_write.py.
- **S5713 presets_remote:** Removed redundant urllib.error.URLError from except (caught by parent OSError).
- **S5852 format_headers:** _RE_PY_IMPORT split into _RE_PY_IMPORT_SIMPLE + _RE_PY_IMPORT_FROM — closes S5852.
- **Audit:** Removed unused ObjectStore and ContentFormatter Protocols from interfaces.py.
- **Audit:** Narrowed domain/__init__.py __all__ to public API only.
- **Audit:** Removed unused re-exports from domain/execution/__init__.py.
- **Audit:** Fixed ARCHITECTURE.md claim about api/config imports.

### v5.2.1: SonarCloud + Audit resolution + test suite dedup
- **SonarCloud: 0 findings.** S1172 x3 (dead config param), S2083 x4 (path validation), S8707 (SafePath passthrough), S5852 x3 (regex refactoring) — all fixed.
- **Audit R1+R2: 25/25 findings closed.** 2 HIGH, 5 MEDIUM, 7 LOW, 5 LEGACY, 6 code quality improvements.
- **ProfileConfig.from_dict():** 6 identical dict-to-dataclass copies deduplicated into one classmethod. Adding a field now requires one edit.
- **SafePath-native atomic_write:** atomic_write_text/bytes accept SafePath directly. All 14 call sites updated — no more .to_path() workarounds.
- **_check_toctou() returns resolved Path:** I/O methods use the resolved path for actual I/O, not self._path. Eliminates S2083 in path_utils.py.
- **Regex refactoring:** _RE_ES6_IMPORT_FROM split into DESTRUCTURE + SIMPLE patterns. _RE_COMMONJS_REQUIRE split into DESTRUCTURE + SIMPLE patterns. _RE_PY_MULTILINE_IMPORT simplified. _C_LIKE_IMPORT_PATTERNS: 6 -> 8 patterns, all safe from polynomial backtracking.
- **Backward-compat removed:** snapshot/snapshots.py (118 lines, 60+ re-exports) deleted. interfaces.py (6 lines, deprecated stub) deleted. All imports updated to direct subpackage paths.
- **Dead code removed:** gatherer_core.py (deprecated re-export). Dead if __name__ block in config/completion.py. dict branch in get_root(). All bare except -> specific exceptions.
- **Global state -> @lru_cache:** gatherer_strategies.get_mode_strategies(), tokenizer._check_tokenizer_plugins(), presets._load_builtin_presets_cached().
- **Stale lock detection:** merge_lock fallback writes PID, checks process liveness before blocking.
- **Test suite dedup:** 12 edge files merged into parents, 6 coverage files renamed, 8 duplicates removed, 4 empty __init__.py removed. test_runner_edge.py (35 tests) merged into test_run_command.py. conftest.py optimized. All docstrings cleaned of version tags and BUG/TC prefixes. 1644 tests, 96% coverage.

### v5.2.0: Package reorganization + type safety
- **domain/ split into 5 subpackages:** cache/, collection/, formatting/, tokenization/, execution/ — 27 files organized by subsystem
- **snapshot/ split into 3 subpackages:** store/, diff/, rename/ — 12 files organized by responsibility
- **config/ split into 3 subpackages:** core/, presets/, setup/ — 10 files organized by domain
- **Dataclass config:** ProfileConfig + ArachnaConfig replace ~200 dict.get() calls with typed field access
- **Enum/Literal types:** CollectionMode, OutputFormat, SplitMode — linters catch typos at development time
- **api/ <-> config/ cycle broken:** api/ no longer imports get_profile/load_config from config/
- **compute_diff_stats moved** to domain/differ_stats.py — pure function, no snapshot/ dependency
- **_sanitize_log centralized** in domain/runner.py — single CRLF sanitization for all logger calls

### v5.1.1: Security hardening + SonarCloud cleanup
- **Command substitution blocked:** $() and backticks rejected in both restricted and pre_commands modes. Prevents allowlist bypass attacks like `git $(rm -rf /)`.
- **CRLF sanitization:** All logger calls that include user-configured commands sanitize \n -> \\n, \r -> \\r before logging. Applied to _handle_dangerous_override, _collect_snapshot_pre_commands, _collect_snapshot_command.
- **TOCTOU protection:** SafePath I/O methods (read_text, write_text, read_bytes, write_bytes) double-check path via resolve() + is_relative_to() at I/O time. Detects symlink swaps between construction and I/O.
- **SafePath.to_path():** Clean SafePath->Path conversions without Path(str(...)) workarounds. All callers updated.
- **Manifest versioning:** _version field in snapshot manifests with migration placeholder. Future versions rejected with clear error.
- **Atomic output:** _write_parts and _write_diff_parts use atomic_write_text for output files.
- **SonarCloud:** S2737, S1481, S7504 fixed. 10 false positives accepted as secure-by-design. 1643 tests, 96% coverage.

### v5.1.0: SafePath + full audit resolution
- **SafePath:** Path wrapper with mandatory root validation in domain/path_utils.py. All file I/O goes through SafePath — validation is structural, not comment-based. Eliminates all SonarCloud S2083/S8707 false positives.
- **CRITICAL fix:** Removed importlib.import_module fallback in tokenizer.py. Unknown tokenizer packages now rejected with clear error.
- **HIGH fix:** Made snapshot_diff functions public — apply_repo_map_to_sections, collect_snapshot_content.
- **MEDIUM decomposition:** formatter.py (605 lines -> 6 sub-modules), snapshot_diff.py (720 lines -> 4 sub-modules + helpers).
- **MEDIUM hardening:** Narrowed except Exception -> specific types in 5 locations.
- **LOW polish:** Atomic writes, KeyError as error, DANGEROUS log -> error, _log_writer -> parameter, threading.Lock, lru_cache.

### v5.0.0: Architecture cleanup
- Renamed watch/ package to snapshot/ (~60 files). Public API: `from arachna import snapshot`.
- Deduplicated DiffSection, cleaned docstrings, narrowed __all__.
- SonarCloud fixes: S1481, S3776 x3, S5145, S8502, S7504.

## Plugin architecture

Plugins are opt-in Python packages. Core stays zero-dep.

User installs: pip install arachna[javascript]
                     |
                     v
              pyproject.toml extras
              tree-sitter, tree-sitter-javascript
                     |
                     v
         differ_structural._check_plugins()
              try: import tree_sitter_javascript
                     |
              ┌──────┴──────┐
              │              │
         ImportError    Success
              │              │
         _HAS_TS_JS    _HAS_TS_JS
         = False       = True
              │              │
              v              v
         text diff    tree-sitter
         (fallback)   structural diff

## Dependencies

**Runtime:** Python 3.11+ stdlib only. Zero external dependencies.
**Optional:** tree-sitter, tiktoken, transformers — installed by user via plugins.
**Dev:** pytest, ruff, pre-commit, pdoc, pytest-cov, hypothesis, psutil, tree-sitter, tiktoken, transformers.

## Testing

1660 tests, 96% coverage. Tests mirror src/arachna/ package structure.

tests/
  domain/       Tests for domain/ modules
  snapshot/     Tests for snapshot/ modules
  api/          Tests for api/ modules
  config/       Tests for config/ modules
  cli/          Tests for cli/ modules
  plugins/      Tests for plugins/ module
  integration/  CLI end-to-end tests
  benchmark/    Performance benchmarks
