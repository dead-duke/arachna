# arachna — Architecture

## Overview

arachna is a context collector for AI. It gathers project files, splits them
by token limits, and writes output files ready for AI consumption.

## Module map

```
__main__.py         CLI entry point, argparse subparsers (collect, snapshot, diff, store, plugins, presets, doctor, init, completion)
plugins.py          Plugin system: environment detector, install/uninstall/list commands
profiler.py         Benchmark runner: measures token savings across all modes
collect_api.py      Public Collection API (programmatic use, write_to_disk param)
collector.py        Orchestrator: gather -> split -> write -> post_commands
gatherer.py         Content assembly: streaming for full mode, in-memory for repo-map/headers
formatter.py        File formatting: markdown/xml/json, language detection, C_LIKE_LANGS/SCRIPT_LANGS
splitter.py         Token-based splitting, oversized section fallback chain, returns (parts, indices) tuple
tokenizer.py        Token estimation with configurable chars_per_token, pluggable tokenizers (tiktoken, transformers)
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
differ_structural.py Structural diff (ast for Python, regex for C-like/script, tree-sitter plugin support)
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

## Plugin architecture (v3.1.0)

Plugins are opt-in Python packages. Core stays zero-dep.

```
User installs: pip install arachna[javascript]
                     │
                     ▼
              pyproject.toml extras
              tree-sitter, tree-sitter-javascript
                     │
                     ▼
         differ_structural._check_plugins()
              try: import tree_sitter_javascript
                     │
              ┌──────┴──────┐
              │              │
         ImportError    Success
              │              │
         _HAS_TS_JS    _HAS_TS_JS
         = False       = True
              │              │
              ▼              ▼
         text diff    tree-sitter
         (fallback)   structural diff
```

Environment detector (plugins.py) recognizes: pipx, poetry, uv, conda, venv, system Python with PEP 668.

## Dependencies

**Runtime:** Python 3.11+ stdlib only. Zero external dependencies.
**Optional:** tree-sitter, tiktoken, transformers — installed by user via plugins.
**Dev:** pytest, ruff, pre-commit, pdoc, pytest-cov, hypothesis, psutil, tree-sitter, tiktoken, transformers.

## Testing

1251 tests, 92% coverage. Plugin code tested with real packages locally,
fallback paths tested in CI without plugins.

```
tests/
  benchmark/       Performance benchmarks (9 tests)
  plugins/         Plugin system tests (environment detector, install commands)
  ...
```
