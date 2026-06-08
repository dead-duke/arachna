# TODO

## v2.8.1 — Code Quality + Testability
- [x] LOW: Decompose watcher.compute_diff — extract _diff_files, _diff_pre_commands, _diff_command
- [x] LOW: Unify _cmd_clean glob patterns — single pattern for all chat-diff formats
- [x] LOW: _RE_C_LIKE_BLOCK refactor — split into language-specific named groups
- [x] LOW: _should_skip_binary refactor — flatten 6 return paths into decision table
- [x] LOW: Replace os.path.basename with pathlib in _diff_pre_commands_structural
- [x] LOW: _write_parts TOC — use section indices instead of content.strip() matching
- [x] LOW: split_sections — add was_truncated warning via logger
- [x] LOW: _filter_by_query — filter pre_commands by default, add include_pre_commands param
- [x] LOW: _detect_renames_and_moves O(N²) — limit similarity to same-extension
- [x] LOW: _format_added — subtract truncation message length from token limit
- [x] LOW: _run_profile — use dataclass return type instead of tuple
- [x] LOW: _read_file_from_store — build {path: hash_spec} dict once, O(1) per file
- [x] LOW: _cmd_snapshot info — use list_snapshots result directly
- [x] LOW: gatherer — warn when both command and directories present
- [x] LOW: runner._log_command — injectable log writer via _write_log
- [x] LOW: _store_root — accept explicit root path parameter
- [ ] Update CHANGELOG for v2.8.1

## v2.8.2 — Design/UX + Final polish
- [ ] LOW: --mode headers naming — clarify README or rename
- [ ] LOW: Add --no-pre-commands / --skip-pre-commands CLI flag
- [ ] LOW: _SAFE_TOKENIZERS — configurable via ARACHNA_SAFE_TOKENIZERS env var
- [ ] LOW: _EXT_LANG — add .hpp, .cmake, .gradle, .lock, .conf
- [ ] LOW: Rate limiting on pre_commands — configurable delay between executions
- [ ] LOW: Warn when pre_command produces no output in snapshot
- [ ] LOW: _load_builtin_presets cache invalidation based on directory mtime
- [ ] LOW: store.py race condition — atomic write for .arachna/.gitignore
- [ ] Update CHANGELOG for v2.8.2

## Backlog
- [ ] Plugin system for custom formatters and tokenizers
- [ ] Web UI for context browsing
- [ ] IDE integration (VSCode extension)
