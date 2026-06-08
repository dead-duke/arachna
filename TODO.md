# TODO

## v2.7.0 — LOW fixes, store, packaging, polish
- [x] LOW-01: _get_audit_log_path — limit traversal depth (5 levels)
- [x] LOW-02: Symlink to .git — check is_symlink() before is_dir()
- [x] LOW-05: _handle_single — replace binary search with direct calculation for default tokenizer
- [x] LOW-06: _split_to_sections — fix inconsistent marker prefix on first element
- [x] LOW-07: store.gc — remove empty subdirectories in objects/
- [x] LOW-08: store._hash_path — only mkdir on write, not read
- [x] LOW-09: store.read_object — better error message for non-zlib data
- [x] LOW-10: Explicit cache deletion for removed files in incremental mode
- [x] LOW-11: Move empty query check before _collect_import_graph call
- [x] LOW-12: _should_skip_binary — handle no-extension binary files (check for null bytes)
- [x] LOW-13: Multi-line import regex fallback for SyntaxError
- [x] LOW-15: _cmd_presets_update — validate local presets.json before merge
- [x] LOW-16: init.run_defaults — always create output_dir
- [x] LOW-17: cache._MAX_HASH_SIZE — make configurable via ARACHNA_MAX_HASH_SIZE env var
- [x] LOW-22: pyproject.toml — add [project.optional-dependencies]
- [x] LOW-23: pyproject.toml — update license field to PEP 639
- [x] LOW-24: CHANGELOG.md — add descriptions for v0.1.4 and v0.1.5
- [x] LOW-25: _cmd_validate — add KeyError guard for get_profile
- [x] LOW-26: store.stats — reuse manifest list, don't glob twice
- [x] MEDIUM-01: _merge_lock — warn if both fcntl and msvcrt unavailable

## Backlog
- [ ] Plugin system for custom formatters and tokenizers
