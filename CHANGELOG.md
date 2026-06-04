# Changelog

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

## v0.1.5 — Shebang Detection
## v0.1.4 — Tests & Bugfixes
## v0.1.3 — Validate & Gitignore
## v0.1.2 — Dry-run, renderer, pre-commit
## v0.1.1 — Tests + fixes
## v0.1.0 — MVP

