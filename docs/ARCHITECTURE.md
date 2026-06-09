# arachna — Architecture

## Overview

arachna is a context collector for AI. It gathers project files, splits them
by token limits, and writes output files ready for AI consumption.

## Module map

```
__main__.py         CLI entry point, argparse, all command handlers
cli_watch.py        Watch CLI handlers (--snapshot, --diff, --store)
collect_api.py      Public Collection API (programmatic use, write_to_disk param)
collector.py        Orchestrator: gather -> split -> write -> post_commands
gatherer.py         Content assembly: streaming for full mode, in-memory for repo-map/headers
formatter.py        File formatting: markdown/xml/json, language detection, C_LIKE_LANGS/SCRIPT_LANGS
splitter.py         Token-based splitting, returns (parts, indices) tuple
tokenizer.py        Token estimation with configurable chars_per_token, pluggable tokenizers
compressor.py       Safe whitespace compression (blank lines, trailing ws)
config.py           .arachna.json loader, profile resolution with extends, defaults
runner.py           Popen-based command execution, dual-mode allowlist, output size limits
renderer.py         Dry-run output formatting
validator.py        Profile validation (errors + warnings)
doctor.py           Full configuration diagnostic
hook.py             Git post-commit hook installer
init.py             Interactive .arachna.json bootstrap
presets.py          Language/engine presets, auto-detection, external presets, mtime-based cache
differ.py           LLM-optimized text diff (markdown + XML), tokenizer-aware truncation
differ_structural.py Structural diff (ast for Python, regex with named groups for C-like/script)
watcher.py          Watch orchestration: snapshots + diffs, decomposed pipeline, relative paths
store.py            Content-addressable store (SHA256 + zlib, dedup, GC, atomic writes, snapshot ID validation)
completion.py       Bash and zsh shell completion
cache.py            Smart hybrid incremental cache (mtime_ns + size + SHA256)
gitignore.py        .gitignore parser for auto-exclusion
api_types.py        Public API dataclasses
api_errors.py       Public API exception classes
watch.py            Public Watch API (programmatic), thin wrapper over watcher + gatherer
store_errors.py     Store subsystem exceptions
```

## Data flow

### Collection — full mode (streaming, v2.9.2)

```
User -> __main__.py -> collector.collect()
                            |
                            v
                       gatherer._assemble_content()
                            |
                   +--------+--------+
                   |                 |
            _collect_pre_commands   _scan_directories
            (run immediately)       (stat only, no read)
                   |                 |
                   v                 v
              first part      _filter_filenames_by_query
                   |                 |
                   v                 v
            pre_commands      _stream_full_mode()
              output          for each file:
                                  read -> format -> compress -> pack
                                  flush part when max_tokens reached
                                              |
                                              v
                                       _write_parts() -> files
```

Memory: O(max_tokens + file_metadata), independent of file count.

### Collection — repo-map/headers mode (in-memory)

```
User -> __main__.py -> collector.collect()
                            |
                            v
                       gatherer._assemble_content()
                            |
            +---------------+---------------+
            |                               |
    _collect_pre_commands           _scan_directories
            |                               |
            v                               v
      run_command()                  read all files
            |                               |
            +-----------+-------------------+
                        |
                        v
              _filter_by_query (full scoring + import chain)
                        |
                        v
              format_file_section (AST/regex parsing)
                        |
                        v
              split_sections -> (parts, indices)
                        |
                        v
              _write_parts() -> files
```

Memory: O(total_content). Suitable for <10K files.

### Watch (arachna --snapshot / --diff)

```
User -> __main__.py -> cli_watch._cmd_snapshot / _cmd_diff
                            |
            +---------------+---------------+
            |                               |
    _cmd_snapshot create              _cmd_diff
            |                               |
    watcher.create_snapshot()      watcher.compute_diff()
            |                               |
    _collect_snapshot_content()     _diff_files_sections()
            |                               |
    +-------+-------+               _diff_pre_commands_sections()
    |               |                       |
    files       pre_commands        _diff_command_section()
    |               |                       |
    v               v                       v
    store.create_snapshot()    differ.compute_diff()
            |                         |
            v                         v
    .arachna/store/          _detect_renames_and_moves()
    snapshots/<id>.json              |
                                     v
                              _group_diff_sections()
                                     |
                                     v
                              _write_diff_parts()
                                     |
                                     v
                              _diff_part_header() summary
```

### Agent API (v2.0.0+)

```
User -> watch.py / collect_api.py
              |
    +---------+---------+
    |                   |
    v                   v
store.py          collector.py
watcher.py        gatherer.py
differ.py         splitter.py
```

collect_api supports `write_to_disk=False` for in-memory-only collection.

## Key design decisions

### 1. Token-based splitting, not line-based

AI models charge by tokens, not lines. Splitting by tokens ensures
each output file fits the model's context window with a safety margin.

### 2. Streaming for full mode, in-memory for parsed modes

Full mode streams: stat -> pack metadata -> read content incrementally.
Memory O(max_tokens). Repo-map/headers stay in-memory — they need
AST/regex parsing before token counting.

### 3. Content-addressable store

Watch snapshots use SHA256 hashing for deduplication. Multiple snapshots
share identical file content. Garbage collection removes unreferenced
objects. Store is auto-gitignored. Paths stored relative to project root
for cross-platform portability.

### 4. Dual-mode command sandbox

Restricted mode (11 commands, no shell) for internal calls. Pre_commands
mode (extended allowlist, shell=True) for user config. Popen-based
execution with max_output_size limits.

### 5. Smart hybrid incremental cache

v2 format: mtime_ns + size for fast path, SHA256 fallback for git checkout.

### 6. Pluggable tokenizer with defense-in-depth

Three validation layers: safe list, import check, top-level statements.

### 7. Presets as data, not code

JSON files in src/arachna/presets/. External presets.json supported.

### 8. Single source of truth for language sets

C_LIKE_LANGS and SCRIPT_LANGS in formatter.py, imported by other modules.

### 9. Unified repo-map pipeline

_apply_repo_map_to_sections in gatherer.py — single implementation.

### 10. Decomposed watcher.compute_diff

Three functions: _diff_files_sections, _diff_pre_commands_sections, _diff_command_section.

### 11. Config inheritance with typed merge

Scalars override, exclude lists append, source lists replace. Warnings on conflicts.

## Environment variables

- ARACHNA_MAX_HASH_SIZE — max file size for SHA256 (default: 10 MB)
- ARACHNA_SAFE_TOKENIZERS — safe tokenizer modules (default: tiktoken,transformers)
- ARACHNA_PRE_COMMAND_DELAY — seconds between pre_commands (default: 0)
- ARACHNA_MAX_OUTPUT_SIZE — max stdout for sandbox commands (default: 10 MB)
- ARACHNA_CHARS_PER_TOKEN — chars per token ratio (default: 4)
- ARACHNA_PRESETS_TIMEOUT — presets fetch timeout (default: 10)

## Dependencies

**Runtime:** Python 3.11+ stdlib only. Zero external dependencies.

**Dev:** pytest, ruff, pre-commit, pdoc, pytest-cov, hypothesis.

## Testing

1121 tests, 92% coverage. Tests use tmp_path + monkeypatch exclusively.
Integration tests run arachna as a subprocess.

```
tests/
  cache/           Cache tests (smart hybrid, SHA256 fallback)
  collector/       Collector tests (collect, merge, lock, TOC, write_to_disk)
  completion/      Shell completion tests
  compressor/      Whitespace compression tests (property-based)
  config/          Config loader + extends + profile tests
  differ/          Text + structural + XML + tokenizer-aware diff tests
  doctor/          Diagnostic tests
  formatter/       Formatting tests (binary, headers, shebang, extensions)
  gatherer/        Collection tests (streaming, query, repo-map)
  gitignore/       Gitignore parser tests
  hook/            Git hook installer tests
  init/            Init + presets tests
  integration/     End-to-end CLI tests (snapshot update, diff)
  main/            CLI handler tests
  presets/         Preset detection + fetch + timeout tests
  renderer/        Dry-run output tests
  runner/          Popen + sandbox + max_output_size + shell=True tests
  splitter/        Token splitter + binary search tests (property-based)
  store/           Content store + validate_snapshot_id tests
  tokenizer/       Tokenizer safety + top-level validation + plugin tests
  validator/       Profile validation tests
  watcher/         Watcher orchestration + isolated + relative paths tests
```
