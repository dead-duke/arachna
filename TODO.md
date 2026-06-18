# TODO

## v4.3.0 — Architecture cleanup + SonarCloud final fixes (details: llm_docs/specs/spec-v4.3.0-architecture-cleanup.md)
- [x] Rename watch/ package to snapshot/ (~60 files)
- [x] Deduplicate DiffSection: differ.py → api_types.py (~15 files)
- [x] Clean up docstrings: remove version tags, standardize to one-line descriptions (~30 files)
- [x] Clean up __all__ exports: narrow to intended public surface (~15 modules)
- [x] Deduplicate split mode dispatch: document distinction, extract common constants
- [x] S1481: unused tokens_by_file → _ in collect.py
- [x] S3776: _cmd_collect_all (18→15) — extract _process_collect_results
- [x] S2737: empty except in collector.py — verify fix
- [x] S3776: clean_manifest (16→15) — extract _clean_numbered_files
- [x] S5145: remove filepath from log in collector.py _write_diff_parts + _write_parts
- [x] S3776: _scan_one_directory (16→15) — extract _scan_directory_pattern
- [x] S8502: set.update() instead of for+add in gatherer_query.py _find_importers
- [x] S7504: document why list() is needed in watcher_diff.py _diff_files_sections

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
