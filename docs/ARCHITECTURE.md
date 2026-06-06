# arachna — Architecture

## Overview

arachna is a context collector for AI. It gathers project files, splits them
by token limits, and writes output files ready for AI consumption.

## Module map

```
__main__.py         CLI entry point, argparse, all command handlers
collect_api.py      Public Collection API (programmatic use)
collector.py        Orchestrator: gather -> split -> write -> post_commands
gatherer.py         Content assembly: pre_commands + directories + files
formatter.py        File formatting: markdown/xml/json, language detection
splitter.py         Token-based splitting, repo-map signature extraction
tokenizer.py        Token estimation (4 chars ~ 1 token) + pluggable tokenizers
compressor.py       Safe whitespace compression (blank lines, trailing ws)
config.py           .arachna.json loader, profile resolution, defaults
runner.py           Sandboxed command execution, allowlist, audit log
renderer.py         Dry-run output formatting
validator.py        Profile validation (errors + warnings)
doctor.py           Full configuration diagnostic
hook.py             Git post-commit hook installer
init.py             Interactive .arachna.json bootstrap
presets.py          Language/engine presets, auto-detection, external presets
differ.py           LLM-optimized text diff (markdown + XML)
differ_structural.py Structural diff (ast for Python, regex for C-like/script)
watcher.py          Watch orchestration: snapshots + diffs
store.py            Content-addressable store (SHA256 + zlib, dedup, GC)
completion.py       Bash and zsh shell completion
cache.py            Smart hybrid incremental cache (mtime_ns + size + SHA256)
gitignore.py        .gitignore parser for auto-exclusion
api_types.py        Public API dataclasses
api_errors.py       Public API exception classes
watch.py            Public Watch API (programmatic)
store_errors.py     Store subsystem exceptions
```

## Data flow

### Collection (arachna --all / --profile X)

```
User -> __main__.py -> collector.collect()
                            |
                            v
                       gatherer._assemble_content()
                            |
                   +--------+--------+
                   |                 |
            _collect_pre_commands   _scan_directories
                   |                 |
                   v                 v
              run_command()    format_file_section()
                   |                 |
                   +--------+--------+
                            |
                            v
                     splitter.split_sections()
                            |
                            v
                     _write_parts() -> files
                            |
                            v
                     _run_post_commands()
```

### Watch (arachna --snapshot / --diff)

```
User -> __main__.py -> _cmd_snapshot / _cmd_diff
                            |
            +---------------+---------------+
            |                               |
    _cmd_snapshot create              _cmd_diff
            |                               |
    watcher.create_snapshot()      watcher.compute_diff()
            |                               |
    _collect_snapshot_content()     _diff_file_sets()
            |                               |
    +-------+-------+               +-------+-------+
    |               |               |               |
    files       pre_commands    old_files      new_files
    |               |               |               |
    v               v               v               v
    store.create_snapshot()    differ.compute_diff()
            |                       |
            v                       v
    .arachna/store/          _detect_renames_and_moves()
    snapshots/<id>.json              |
                                     v
                              _group_diff_sections()
                                     |
                                     v
                              _write_diff_parts()
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

## Key design decisions

### 1. Token-based splitting, not line-based

AI models charge by tokens, not lines. Splitting by tokens ensures
each output file fits the model's context window with a safety margin.

### 2. Dense packing via split_sections()

In v1.4.1, split_sections() replaced separate pre_commands and file
splitting. All sections are collected into a single list and packed
densely — every part except the last is >= 50% of max_tokens.

### 3. Content-addressable store

Watch snapshots use SHA256 hashing for deduplication. Multiple snapshots
share identical file content. Garbage collection removes unreferenced
objects. Store is auto-gitignored (.arachna/.gitignore contains "*").

### 4. Read-only command sandbox

All shell commands are validated against a strict allowlist. No interpreters
(python, node, ruby), no filesystem modification (mkdir, chmod, rm).
Commands with shell metacharacters run with shell=True after validation.

### 5. Smart hybrid incremental cache

v2 cache format uses mtime_ns + size for fast path (99% of checks skip
hashing). SHA256 fallback detects false positives (git checkout, touch).

### 6. Pluggable tokenizer with deny-by-default security

load_tokenizer() only allows: "default", whitelisted libraries (tiktoken,
transformers), or local .py files. Stdlib modules and suspicious names
are blocked. No fallback to sys.modules.

### 7. Presets as data, not code

Each preset is a JSON file in src/arachna/presets/. No hardcoded
SERVICE_PRESETS set. External presets.json can override or add presets.
fetch_presets() + merge_presets() enable remote updates.

## Dependencies

**Runtime:** Python 3.11+ stdlib only. Zero external dependencies.

**Dev:** pytest, ruff, pre-commit, pdoc, pytest-cov.

## Testing

907 tests, 92% coverage. Tests use tmp_path + monkeypatch exclusively —
no os.chdir, no system dependencies, no real git commands. Integration
tests run arachna as a subprocess.

```
tests/
  cache/           Cache tests (smart hybrid, edge cases)
  collector/       Collector tests (collect, merge, lock, TOC, diff parts)
  completion/      Shell completion tests
  compressor/      Whitespace compression tests
  config/          Config loader + profile tests
  differ/          Text + structural + XML diff tests
  doctor/          Diagnostic tests
  formatter/       Formatting tests (binary, headers, shebang, verbose)
  gatherer/        Collection tests (incremental, query, repo-map)
  gitignore/       Gitignore parser tests
  hook/            Git hook installer tests
  init/            Init + presets tests
  integration/     End-to-end CLI tests
  main/            CLI handler tests (all commands)
  presets/         Preset detection + fetch + merge tests
  renderer/        Dry-run output tests
  runner/          Command execution + sandbox tests
  splitter/        Token splitter + signature tests
  store/           Content store + snapshots tests
  tokenizer/       Tokenizer safety + plugin tests
  validator/       Profile validation tests
  watcher/         Watcher orchestration tests
```
