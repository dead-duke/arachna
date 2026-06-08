# TODO

## v2.8.0 — Security + Architecture core (details: llm_docs/specs/spec-v2.8.0-security-architecture.md)
- [ ] HIGH: Log injection fix — sanitize \n in _log_command
- [ ] HIGH: RCE via find -exec — remove find from _ALLOWED_COMMANDS, remove env/hg/svn
- [ ] MEDIUM: Single source of truth for _C_LIKE_LANGS and _SCRIPT_LANGS — define in formatter.py, import in differ_structural.py, splitter.py, watch.py
- [ ] MEDIUM: Unify three repo-map implementations — single pipeline shared by gatherer, differ_structural, watch
- [ ] MEDIUM: Single compute_diff engine — watcher.compute_diff as engine, watch.compute_diff as wrapper
- [ ] MEDIUM: Fix tokenizer passthrough in _cmd_diff — pass tokenizer to _write_diff_parts
- [ ] MEDIUM: DRY _format_scanned_files and _collect_specific_files — extract _format_file_list
- [ ] MEDIUM: Deduplicate --output-dir / -o parsing in cli_watch.py
- [ ] MEDIUM: Deduplicate hash collection loop in stats() and gc() — extract _collect_referenced_hashes
- [ ] MEDIUM: watch.py _parse_blocks deduplication — use dispatch from differ_structural
- [ ] MEDIUM: Cache find_config with @lru_cache
- [ ] Update CHANGELOG for v2.8.0

## v2.8.1 — Code Quality + Testability (details: llm_docs/specs/spec-v2.8.1-code-quality.md)
- [ ] LOW: Decompose watcher.compute_diff — extract _diff_files, _diff_pre_commands, _diff_command
- [ ] LOW: Unify _cmd_clean glob patterns — single pattern for all chat-diff formats
- [ ] LOW: _RE_C_LIKE_BLOCK refactor — split into language-specific patterns
- [ ] LOW: _should_skip_binary refactor — flatten 6 return paths into decision table
- [ ] LOW: Replace os.path.basename with pathlib in _diff_pre_commands_structural
- [ ] LOW: _write_parts TOC — use section indices instead of content.strip() matching
- [ ] LOW: split_sections — add was_truncated warning via logger
- [ ] LOW: Rename mode "headers" to "full-with-headers" or document clearly
- [ ] LOW: _filter_by_query — add --include-pre-commands flag, default to filtering pre_commands
- [ ] LOW: _detect_renames_and_moves O(N²) — limit to same-extension + add --no-rename-detect flag
- [ ] LOW: _format_added — subtract truncation message length from token limit
- [ ] LOW: _run_profile — use dataclass return type instead of tuple
- [ ] LOW: _read_file_from_store — build {path: hash_spec} dict once, not O(N) per file
- [ ] LOW: _cmd_snapshot info — use list_snapshots result directly, avoid double manifest load
- [ ] LOW: gatherer — warn when both command and directories present
- [ ] LOW: runner._log_command — injectable log writer, StringIO in tests
- [ ] LOW: watcher.compute_diff — isolated unit tests via mock
- [ ] LOW: presets.fetch_presets — configurable timeout test
- [ ] LOW: _collect_import_graph — cache per file list
- [ ] LOW: _is_binary_allowed — direct unit tests
- [ ] LOW: cache.get_changed_files — explicit test for mtime within tolerance + size differs
- [ ] LOW: _diff_file_sets — direct unit test for modifications-only scenario
- [ ] LOW: _normalize_path — store relative paths, test cross-platform portability
- [ ] LOW: _store_root — accept explicit root path parameter
- [ ] Update CHANGELOG for v2.8.1

## v2.8.2 — Design/UX + Final polish (details: llm_docs/specs/spec-v2.8.2-design-ux.md)
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
