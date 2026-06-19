# TODO

## v5.1.1 — Quick fixes from audit + SonarCloud
- [ ] MEDIUM: Add _version field to snapshot manifests in store.py — follow cache.py pattern
- [ ] LOW: Use atomic_write_text for output files in collector.py _write_parts and _write_diff_parts
- [ ] LOW: Remove double clean_manifest in _cmd_collect_all — add skip_clean parameter
- [ ] S2737: Remove try-except from fallback lock_fn in collector.py — let OSError propagate naturally
- [ ] S1481: Replace unlock_fn with _ in _merge_lock
- [ ] S7504: Replace list(old_files.keys()) with set(old_files) in snapshot_diff_files.py
- [ ] TOCTOU hardening: Add resolve() + is_relative_to() double-check in SafePath I/O methods
- [ ] SafePath: Add to_path() method — clean up all Path(str(safepath)) conversions across project
- [ ] S5145: Sanitize CRLF in _handle_dangerous_override BEFORE logger.error
- [ ] S5145: Sanitize CRLF in _collect_snapshot_pre_commands and _collect_snapshot_command logger.warning calls
- [ ] S2076: Block command substitution $() and backticks in pre_commands mode
- [ ] Accept all other S2083/S8707/S5145/S2076 findings in SonarCloud

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
