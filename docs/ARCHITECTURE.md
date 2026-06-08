# arachna — Architecture

## Overview

arachna is a context collector for AI. It gathers project files, splits them
by token limits, and writes output files ready for AI consumption.

## Module map

```
__main__.py         CLI entry point, argparse, all command handlers
cli_watch.py        Watch CLI handlers (--snapshot, --diff, --store)
collect_api.py      Public Collection API (programmatic use)
collector.py        Orchestrator: gather -> split -> write -> post_commands
gatherer.py         Content assembly: pre_commands + directories + files, repo-map pipeline
formatter.py        File formatting: markdown/xml/json, language detection, C_LIKE_LANGS/SCRIPT_LANGS
splitter.py         Token-based splitting, repo-map signature extraction
tokenizer.py        Token estimation (4 chars ~ 1 token) + pluggable tokenizers, configurable safe list
compressor.py       Safe whitespace compression (blank lines, trailing ws)
config.py           .arachna.json loader, profile resolution, defaults, @lru_cache
runner.py           Sandboxed command execution, dual-mode allowlist, audit log, injectable log writer
renderer.py         Dry-run output formatting
validator.py        Profile validation (errors + warnings)
doctor.py           Full configuration diagnostic
hook.py             Git post-commit hook installer
init.py             Interactive .arachna.json bootstrap
presets.py          Language/engine presets, auto-detection, external presets, mtime-based cache
differ.py           LLM-optimized text diff (markdown + XML)
differ_structural.py Structural diff (ast for Python, regex with named groups for C-like/script)
watcher.py          Watch orchestration: snapshots + diffs, decomposed pipeline
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

## Key design decisions

### 1. Token-based splitting, not line-based

AI models charge by tokens, not lines. Splitting by tokens ensures
each output file fits the model's context window with a safety margin.

### 2. Dense packing via split_sections()

All sections are collected into a single list and packed densely —
every part except the last is >= 50% of max_tokens. Section indices
returned for TOC generation without content matching.

### 3. Content-addressable store

Watch snapshots use SHA256 hashing for deduplication. Multiple snapshots
share identical file content. Garbage collection removes unreferenced
objects. Store is auto-gitignored (.arachna/.gitignore contains "*").
Atomic writes for both .gitignore and objects (tempfile + os.replace).
Snapshot IDs validated against path traversal (regex ^[\w][\w.-]*$).

### 4. Dual-mode command sandbox

Commands execute in two security levels:

- **Restricted mode** (allow_file_args=False): internal calls from store,
  watcher, gatherer. 11 commands: echo, pwd, date, whoami, id, uname,
  which, true, false, test, [. No shell metacharacters, no shell=True.
  Protects against injection via snapshot names, preset URLs, and other
  external input.

- **Pre_commands mode** (allow_file_args=True): user's .arachna.json.
  Extended allowlist: cat, tree, git, grep, sort, wc, head, tail, diff,
  find, and more. Shell=True with pipes and redirection allowed. User
  controls the config — blocking 2>/dev/null would be theatre security.

Audit log with newline sanitization. Blocked patterns for dangerous
commands. No interpreters (python, node, ruby) in either mode.

### 5. Smart hybrid incremental cache

v2 cache format uses mtime_ns + size for fast path (99% of checks skip
hashing). SHA256 fallback detects false positives (git checkout, touch).
Configurable hash size limit via ARACHNA_MAX_HASH_SIZE env var.

### 6. Pluggable tokenizer with defense-in-depth

load_tokenizer() validates through three layers: module name against
safe list (configurable via ARACHNA_SAFE_TOKENIZERS env var), imports
via ast.parse, and top-level statements — only FunctionDef, ClassDef,
Import allowed. No sys.modules fallback. Deny by default.

### 7. Presets as data, not code

Each preset is a JSON file in src/arachna/presets/. No hardcoded sets.
External presets.json can override or add presets. fetch_presets() +
merge_presets() enable remote updates. URL validated (http/https only).
Cache invalidates on directory mtime.

### 8. Single source of truth for language sets

C_LIKE_LANGS and SCRIPT_LANGS are defined once in formatter.py and
imported by differ_structural, splitter, and watch. Adding a new
language requires editing only one file.

### 9. Unified repo-map pipeline

_apply_repo_map_to_sections in gatherer.py is the single repo-map diff
pipeline, shared by collect, structural diff, and watch diff. Pre-generated
headers avoid double ast.parse.

### 10. Decomposed watcher.compute_diff

Split into three single-responsibility functions: _diff_files_sections,
_diff_pre_commands_sections, _diff_command_section. Each handles one
content type.

## Environment variables

- ARACHNA_MAX_HASH_SIZE — max file size in bytes for SHA256 hashing (default: 10 MB)
- ARACHNA_SAFE_TOKENIZERS — comma-separated safe tokenizer modules (default: tiktoken,transformers)
- ARACHNA_PRE_COMMAND_DELAY — seconds between pre_commands (default: 0, no delay)

## Dependencies

**Runtime:** Python 3.11+ stdlib only. Zero external dependencies.

**Dev:** pytest, ruff, pre-commit, pdoc, pytest-cov, hypothesis.

## Testing

1071 tests, 92% coverage. Tests use tmp_path + monkeypatch exclusively —
no os.chdir, no system dependencies, no real git commands. Integration
tests run arachna as a subprocess.

```
tests/
  cache/           Cache tests (smart hybrid, edge cases)
  collector/       Collector tests (collect, merge, lock, TOC, diff parts)
  completion/      Shell completion tests
  compressor/      Whitespace compression tests (property-based)
  config/          Config loader + profile tests (cached, isolated)
  differ/          Text + structural + XML diff tests
  doctor/          Diagnostic tests
  formatter/       Formatting tests (binary, headers, shebang, extensions)
  gatherer/        Collection tests (incremental, query, repo-map)
  gitignore/       Gitignore parser tests
  hook/            Git hook installer tests
  init/            Init + presets tests
  integration/     End-to-end CLI tests
  main/            CLI handler tests (all commands, --no-pre-commands, URL validation)
  presets/         Preset detection + fetch + merge tests
  renderer/        Dry-run output tests
  runner/          Command execution + sandbox + restricted mode + pre_commands tests
  splitter/        Token splitter + signature tests (property-based)
  store/           Content store + snapshots + validate_snapshot_id tests
  tokenizer/       Tokenizer safety + top-level validation + plugin + env tests
  validator/       Profile validation tests
  watcher/         Watcher orchestration + diff + rename + pre_commands tests
```
