# TODO

## v4.2.1 — SonarCloud cleanup (details: llm_docs/specs/spec-v4.2.1-sonarcloud-cleanup.md)
- [ ] S3776: _cmd_collect_all (17→15) — extract _collect_one_profile
- [ ] S3776: _cmd_collect_validate (19→15) — extract _resolve_profiles + _validate_and_print
- [ ] S3776: _cmd_manifest (17→15) — extract _manifest_json + _manifest_text
- [ ] S3776: print_doctor (16→15) — extract _print_profile_results
- [ ] S3776: _parse_python_imports_fallback (18→15) — extract _parse_import_stmt + _parse_multiline_import
- [ ] S3776: _parse_script (16→15) — extract _parse_script_deps + _parse_script_exports
- [ ] S3776: _handle_read_error (16→15) — extract _handle_unicode_error + _handle_verbose_skip
- [ ] S3776: _scan_directories (25→15) — extract _scan_one_directory
- [ ] S3776: _parse_gitignore_lines (17→15) — extract _parse_one_gitignore_line
- [ ] S3776: _expand_import_chain (19→15) — extract _find_importers
- [ ] S3776: _build_parts_for_sections (18→15) — extract _handle_oversized_in_build + _append_or_start_new
- [ ] S3776: _collect_referenced_hashes (16→15) — extract _collect_hashes_from_dict
- [ ] S3776: _diff_pre_commands_line (18→15) — extract _append_diff_lines
- [ ] S3776: _diff_files_sections (18→15) — extract _build_snapshot_files_dict + _build_target_files_dict
- [ ] S5843: _RE_ES6_IMPORT (23→20) — split into _RE_ES6_IMPORT_FROM + _RE_ES6_IMPORT_BARE
- [ ] S2737: empty except in collector.py — add comment
- [ ] S1066: merge if in _handle_read_error — verify fix from v4.2.0
- [ ] S2083: validate path in print_collected (_helpers.py), _write_config (init.py), _write_parts (collector.py), _write_diff_parts (collector.py), clean_manifest (collector.py), list_snapshots (store.py)
- [ ] S8707: validate output_dir in _write_config (init.py)
- [ ] S1481: unused 'deleted' → '_' in test_cache_os_error_handling.py
- [ ] S3516: verify _format_skip_message fix picked up by SonarCloud in next scan

## v4.3.0 — Architecture cleanup (details: llm_docs/specs/spec-v4.3.0-architecture-cleanup.md)
- [ ] Rename watch/ package to snapshot/ (~60 files)
- [ ] Deduplicate DiffSection: differ.py → api_types.py (~15 files)
- [ ] Clean up docstrings: remove version tags, standardize to one-line descriptions (~30 files)
- [ ] Clean up __all__ exports: narrow to intended public surface (~15 modules)
- [ ] Deduplicate split mode dispatch: document distinction, extract common constants

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
