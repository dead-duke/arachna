# TODO

## v2.5.0 — Security, architecture, watcher fixes
- [ ] HIGH-01: Fix XML injection in _format_xml_diff, _format_added, _format_deleted (use xml.sax.saxutils.escape)
- [ ] HIGH-02: _is_safe_tokenizer — add static import analysis via ast.parse for local .py files
- [ ] HIGH-03: Extract Watch handlers from __main__.py into cli_watch.py
- [ ] HIGH-04: Fix _cmd_diff_all — pass name_template to collect() instead of renaming after
- [ ] MEDIUM-02: Error when --diff --all and --from are used together
- [ ] MEDIUM-07: _normalize_path — collapse double slashes, strip ./ prefix
- [ ] MEDIUM-08: _path_matches_profile — normalize paths before comparison
- [ ] MEDIUM-09: _collect_snapshot_content — skip files outside cwd, warn instead of absolute paths
- [ ] MEDIUM-10: _diff_pre_commands_line — use list comparison instead of set (preserve order)
- [ ] LOW-14: _diff_pre_commands_structural — use os.path.basename for tree detection
- [ ] MEDIUM-18: Restore informative warning messages in presets.py
- [ ] MEDIUM-06: watcher._apply_repo_map_diff — log when falling back to text diff

## v2.6.0 — Code quality, formatter, differ, test coverage
- [ ] MEDIUM-03: Extract duplicated repo-map logic into _apply_repo_map_to_section
- [ ] MEDIUM-04: _assemble_command_content — accept query/mode parameters for symmetry
- [ ] MEDIUM-05: _assemble_file_content — split into pipeline (collect -> filter -> compress -> split)
- [ ] MEDIUM-11: Added files in diff — consider token limit awareness
- [ ] MEDIUM-12: _RE_PY_IMPORT — handle multiple imports on one line (import a, b)
- [ ] MEDIUM-13: Add .tsx and .jsx to _EXT_LANG
- [ ] MEDIUM-14: PHP use-statements in _RE_C_LIKE_IMPORT
- [ ] MEDIUM-15: Go type block name — capture first \w+ after type, not second
- [ ] MEDIUM-16: Rust generics with braces — improve regex
- [ ] MEDIUM-17: collector._build_toc — build from section names, not content matching
- [ ] MEDIUM-19: watch.py — raise coverage from 78% to 90%+
- [ ] MEDIUM-20: collector.py — raise coverage from 87% to 90%+
- [ ] LOW-18: Add property-based tests for tokenizer, compressor, splitter
- [ ] LOW-19: test_merge_lock_windows_msvcrt — mock on Unix
- [ ] LOW-20: Test presets.json with UTF-16 encoding
- [ ] LOW-21: Unicode edge case tests for tokenizer

## v2.7.0 — LOW fixes, store, packaging, polish
- [ ] LOW-01: _get_audit_log_path — limit traversal depth
- [ ] LOW-02: Symlink to .git — check is_symlink() before is_dir()
- [ ] LOW-03: Makefile — remove ?= for SNAPSHOT, require explicit value
- [ ] LOW-04: Makefile — fix python3 portability for Windows
- [ ] LOW-05: _handle_single — replace binary search with direct calculation
- [ ] LOW-06: _split_to_sections — fix inconsistent marker prefix on first element
- [ ] LOW-07: store.gc — remove empty subdirectories in objects/
- [ ] LOW-08: store._hash_path — only mkdir on write, not read
- [ ] LOW-09: store.read_object — better error message for non-zlib data
- [ ] LOW-10: Explicit cache deletion for removed files in incremental mode
- [ ] LOW-11: Move empty query check before _collect_import_graph call
- [ ] LOW-12: _should_skip_binary — handle no-extension binary files
- [ ] LOW-13: Multi-line import regex fallback for SyntaxError
- [ ] LOW-15: _cmd_presets_update — validate local presets.json before merge
- [ ] LOW-16: init.run_defaults — always create output_dir
- [ ] LOW-17: cache._MAX_HASH_SIZE — make configurable
- [ ] LOW-22: pyproject.toml — add [project.optional-dependencies]
- [ ] LOW-23: pyproject.toml — update license field to PEP 639
- [ ] LOW-24: CHANGELOG.md — add descriptions for v0.1.4 and v0.1.5
- [ ] LOW-25: _cmd_validate — add KeyError guard for get_profile
- [ ] LOW-26: store.stats — reuse manifest list, don't glob twice
- [ ] LOW-27: XML escaping in _format_added and _format_deleted (same fix as HIGH-01)
- [ ] MEDIUM-01: _merge_lock — warn if both fcntl and msvcrt unavailable

## Backlog
- [ ] Plugin system for custom formatters and tokenizers (v3.0)

