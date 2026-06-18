# arachna — Architecture

## Overview

arachna is a context layer for AI workflows: snapshots, diffs, profiles. Collect once, diff forever.

## Package structure (v5.1.0)

src/arachna/
  __init__.py           Version + public API re-exports
  __main__.py           CLI entry point: build_argparse() + main() dispatch
  interfaces.py         Backward-compat re-export from domain/

  domain/               Pure data transformations, no I/O dependencies
    api_types.py        Public API dataclasses (DiffSection, DiffStats, etc.)
    atomic_write.py     Atomic file writes (mkstemp + os.replace)
    cache.py            Smart hybrid incremental cache (mtime_ns + size + SHA256)
    collector.py        Orchestrator: gather -> split -> write -> post_commands
    compressor.py       Safe whitespace compression (str.rstrip, no regex)
    format_language.py  Language detection, C_LIKE_LANGS, SCRIPT_LANGS, _EXT_LANG
    format_binary.py    Binary file detection and base64 formatting
    format_headers.py   Deps/exports extraction for all languages (regex + AST)
    format_output.py    File section formatting (markdown/xml/json), SafePath integration
    format_exclude.py   fnmatch exclusion matching with directory support
    format_sigs.py      Signature formatting for repo-map mode
    formatter.py        Re-exports from all format_* sub-modules (backward-compatible)
    gatherer.py         Facade over gatherer_files + gatherer_commands + gatherer_query + gatherer_strategies
    gatherer_files.py   Directory scanning, file formatting, exclude patterns
    gatherer_commands.py  Command execution: pre_commands, gather_files, gather_command
    gatherer_query.py   Query pipeline: import graph, scoring, filtering
    gatherer_strategies.py  Strategy pattern: FullModeStrategy with _CollectParams dataclass
    gitignore.py        .gitignore parser for auto-exclusion
    interfaces.py       Protocol definitions: Tokenizer, ObjectStore, ContentFormatter
    language_dispatch.py  HEADER_PARSERS + BLOCK_PARSERS mappings, regex timeout
    path_utils.py       Path validation (validate_path) + SafePath class
    runner.py           Popen-based command execution, dual-mode allowlist, decomposed helpers
    splitter.py         Token-based splitting, oversized section fallback, pack_into_parts
    tokenizer.py        Token estimation, pluggable tokenizers, safety validation

  config/               Configuration, presets, init, validation
    __init__.py         VALID_SPLIT_MODES + COLLECTION_MODES constants
    completion.py       Bash and zsh shell completion (argparse subparsers)
    config.py           .arachna.json loader, profile resolution with extends
    doctor.py           Full diagnostic: run_doctor(project_root, config)
    hook.py             Git post-commit hook installer
    init.py             Interactive .arachna.json bootstrap
    presets.py          Language/engine presets, auto-detection, validation
    presets_remote.py   Remote presets: fetch_presets + merge_presets
    profiler.py         Benchmark runner: measures token savings across modes
    remote.py           Remote repository collection (git clone + collect)
    validator.py        Profile validation

  snapshot/             Snapshots, diff, store, benchmarks
    benchmarks.py       Plugin benchmarks (structural-diff, tiktoken)
    differ.py           LLM-optimized text diff (markdown + XML), line numbers
    differ_structural.py  Structural diff: Python AST, C-like regex, tree-sitter plugin
    store.py            Content-addressable store (SHA256 + zlib, dedup, GC)
    store_errors.py     Store subsystem exceptions
    snapshots.py        Re-exports from all snapshot_diff_* sub-modules
    snapshot_diff.py    Diff computation — orchestration + grouping (120 lines)
    snapshot_diff_helpers.py  Path normalization (_rel_path, _normalize_path)
    snapshot_diff_files.py    File collection, diff sections, path matching, store I/O
    snapshot_diff_commands.py Pre_commands/command execution and diff strategies
    snapshot_diff_repo_map.py Repo-map transformation for diff sections
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
API layer imports from domain/ and snapshot/.
Snapshot layer imports from domain/.
Config layer imports from domain/.
Domain layer imports only from stdlib and other domain/ modules.

No circular dependencies. No lazy imports between packages.

## Key architectural decisions

### v5.1.0: SafePath + full audit resolution
- **SafePath:** Path wrapper with mandatory root validation in domain/path_utils.py. All file I/O goes through SafePath — validation is structural, not comment-based. Eliminates all SonarCloud S2083/S8707 false positives. Refactored into collector.py, store.py, cli/*.py, config/*.py, cache.py, format_output.py.
- **CRITICAL fix:** Removed importlib.import_module fallback in tokenizer.py. Unknown tokenizer packages now rejected with clear error. Only local files (validated via AST) + known-safe tokenizers allowed.
- **HIGH fix:** Made snapshot_diff functions public — apply_repo_map_to_sections, collect_snapshot_content. Public API no longer imports underscored private functions.
- **MEDIUM decomposition:** formatter.py (605 lines → 6 sub-modules: format_language, format_binary, format_headers, format_output, format_exclude, format_sigs). snapshot_diff.py (720 lines → 4 sub-modules + helpers: snapshot_diff_files, snapshot_diff_commands, snapshot_diff_repo_map, snapshot_diff_helpers).
- **MEDIUM hardening:** Narrowed except Exception → specific types in atomic_write.py, cache.py, hook.py, snapshot_diff.py.
- **LOW polish:** Atomic writes in init.py/presets.py/_helpers.py, KeyError counted as error in validation, DANGEROUS log elevated to error, _log_writer → parameter injection, threading.Lock for all global state (4 modules), importlib.reload → @lru_cache.
- **SonarCloud:** S1481, S2737, S7504 fixed. 1616 tests, 96% coverage, 0 SonarCloud findings.

### v5.0.0: Architecture cleanup
- Renamed watch/ package to snapshot/ — watch implied active monitoring, actual functionality is snapshot management (create, store, diff, delete). ~60 files affected.
- Deduplicated DiffSection: differ.py now imports from domain/api_types.py instead of defining its own copy. ~15 files updated.
- Docstrings cleaned: version tags removed from module docstrings, standardized to one-line descriptions. ~30 files.
- __all__ narrowed to intended public API surface. ~15 modules.
- Split mode dispatch documented: _SPLIT_MODE_DISPATCH (splitter.py) handles token-limit splitting, _get_mode_strategies (gatherer_strategies.py) handles collection strategy. Both are distinct.
- SonarCloud fixes: S1481, S3776 x3, S5145, S8502, S7504.

### v4.2.0: Code quality refactoring
- _CollectParams dataclass: 14 params -> 1 object in _FullModeStrategy
- Module splits: gatherer_core -> gatherer_files + gatherer_commands, watcher -> snapshot_diff + snapshot_rename, presets -> presets_remote
- _BLOCK_PATTERNS: named groups -> numbered for simpler regex
- _RE_C_LIKE_IMPORT -> _RE_C_LIKE_IMPORT_CHAIN (5 single-purpose patterns)
- compressor.py: _RE_TRAILING_WS regex -> str.rstrip()
- remote.py: domain/ -> config/ (layer violation fix)
- path_utils.py: validate_path() for S2083 path injection
- Cognitive complexity: all 35+ C-functions -> B
- diff --line-numbers: line numbers in REMOVED/ADDED blocks

### Strategy pattern for collection modes
FullModeStrategy, RepoMapModeStrategy, HeadersModeStrategy — each encapsulates
its own import graph cache. Mode dispatch via _get_mode_strategies() which
lazy-initializes the mapping.

### Dual-mode command sandbox
Restricted mode (internal calls): 11 safe commands, no shell, no pipes.
Pre_commands mode (user config): extended read-only allowlist, shell=True, pipes allowed.
See docs/SECURITY.md for full threat model.

### Content-addressable store
Files stored by SHA256 hash. Deduplication across snapshots.
Atomic writes via mkstemp + os.replace. Snapshots share identical objects.

### Smart hybrid incremental cache
mtime_ns + size fast path (99% of cases). SHA256 fallback for false positives
(git checkout, touch). Automatic v1->v2 migration.

### Language dispatch
C_LIKE_LANGS and SCRIPT_LANGS defined once in format_language.py. HEADER_PARSERS
and BLOCK_PARSERS mappings in language_dispatch.py cover all languages via
get_header_parser() and get_block_parser(). Adding a language requires
editing format_language.py only.

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

1616 tests, 96% coverage. Tests mirror src/arachna/ package structure.

tests/
  domain/       Tests for domain/ modules (SafePath: 14 tests)
  snapshot/     Tests for snapshot/ modules
  api/          Tests for api/ modules
  config/       Tests for config/ modules
  cli/          Tests for cli/ modules
  plugins/      Tests for plugins/ module
  integration/  CLI end-to-end tests (7 snapshot edge case tests)
  benchmark/    Performance benchmarks
