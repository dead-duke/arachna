# arachna — Architecture

## Overview

arachna is a context collector for AI. It gathers project files, splits them
by token limits, and writes output files ready for AI consumption.

## Module map

### CLI layer — src/arachna/cli/

__init__.py         COMMAND_HANDLERS registry, @register decorator
_helpers.py         Shared helpers: list_profiles, parse_output_dir, print_collected, write_manifest, format_profile_section
collect.py          collect --profile, --all, --list, --validate, --clean handlers
snapshot.py         snapshot create/list/update/delete/info/rename handlers
diff.py             diff --from, --to, --all handlers
store.py            store stats, store gc handlers
plugins.py          plugins list/install/uninstall handlers
presets.py          presets update handler
doctor.py           doctor handler
init.py             init handler + _dispatch_init for --install-hook
completion.py       completion bash/zsh handler
profile.py          profile (benchmark) handler
manifest.py         manifest --json handler

### Core modules — src/arachna/

__main__.py         CLI entry point: build_argparse() + main() dispatch
interfaces.py       Protocol definitions: Tokenizer, ObjectStore, ContentFormatter
collect_api.py      Public Collection API (programmatic use, write_to_disk param)
collector.py        Orchestrator: gather -> split -> write -> post_commands
gatherer.py         Content assembly: Strategy pattern (FullModeStrategy, RepoMapModeStrategy, HeadersModeStrategy)
formatter.py        File formatting: markdown/xml/json, language detection, C_LIKE_LANGS/SCRIPT_LANGS
splitter.py         Token-based splitting, oversized section fallback chain, pack_into_parts
tokenizer.py        Token estimation, configurable chars_per_token, pluggable tokenizers
compressor.py       Safe whitespace compression
config.py           .arachna.json loader, profile resolution with extends, get_profile(name, config)
runner.py           Popen-based command execution, dual-mode allowlist, run_pre_commands try-except
renderer.py         Dry-run output formatting
validator.py        Profile validation
doctor.py           Full diagnostic: run_doctor(project_root, config)
hook.py             Git post-commit hook installer
init.py             Interactive .arachna.json bootstrap
presets.py          Language/engine presets, auto-detection, external presets, fetch_presets(timeout)
differ.py           LLM-optimized text diff (markdown + XML), tokenizer-aware truncation
differ_structural.py Structural diff: Python (ast), C-like (_BLOCK_PATTERNS chain), script (regex), tree-sitter plugin
watcher.py          Watch orchestration: decomposed compute_diff, rename/move detection
store.py            Content-addressable store (SHA256 + zlib, dedup, GC, atomic writes)
completion.py       Bash and zsh shell completion
cache.py            Smart hybrid incremental cache (mtime_ns + size + SHA256)
gitignore.py        .gitignore parser for auto-exclusion
api_types.py        Public API dataclasses
api_errors.py       Public API exception classes
watch.py            Public Watch API (programmatic), thin wrapper over watcher + gatherer
store_errors.py     Store subsystem exceptions
plugins.py          Plugin system: environment detector, install/uninstall/list commands
profiler.py         Benchmark runner: measures token savings across all modes

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

Environment detector (plugins.py) recognizes: pipx, poetry, uv, conda, venv, system Python with PEP 668.

## Dependencies

**Runtime:** Python 3.11+ stdlib only. Zero external dependencies.
**Optional:** tree-sitter, tiktoken, transformers — installed by user via plugins.
**Dev:** pytest, ruff, pre-commit, pdoc, pytest-cov, hypothesis, psutil, tree-sitter, tiktoken, transformers.

## Testing

1429 tests, 93% coverage. Plugin code tested with real packages locally,
fallback paths tested in CI without plugins.

tests/
  benchmark/       Performance benchmarks
  cache/           Cache tests (smart hybrid incremental)
  collector/       Collection orchestrator tests
  completion/      Shell completion tests
  compressor/      Whitespace compression tests
  config/          Config loader + extends tests
  differ/          Text diff + structural diff tests
  doctor/          Diagnostic tests
  formatter/       File formatting + headers tests
  gatherer/        Content assembly tests
  gitignore/       Gitignore parser tests
  hook/            Git hook installer tests
  init/            Init + presets tests
  integration/     CLI end-to-end tests
  main/            CLI handler tests
  plugins/         Plugin system tests
  presets/         Presets detection + fetch tests
  renderer/        Dry-run renderer tests
  runner/          Command execution sandbox tests
  splitter/        Token splitting + oversized section tests
  store/           Content-addressable store tests
  tokenizer/       Token estimation + plugin tests
  validator/       Profile validation tests
  watcher/         Watch orchestration tests
