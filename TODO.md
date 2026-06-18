# TODO

## v4.3.0 — Architecture cleanup + SonarCloud final fixes (details: llm_docs/specs/spec-v4.3.0-architecture-cleanup.md)
- [ ] Rename watch/ package to snapshot/ (~60 files)
- [ ] Deduplicate DiffSection: differ.py → api_types.py (~15 files)
- [ ] Clean up docstrings: remove version tags, standardize to one-line descriptions (~30 files)
- [ ] Clean up __all__ exports: narrow to intended public surface (~15 modules)
- [ ] Deduplicate split mode dispatch: document distinction, extract common constants
- [ ] S1481: unused tokens_by_file → _ in collect.py
- [ ] S3776: _cmd_collect_all (18→15) — extract _process_collect_results
- [ ] S2737: empty except in collector.py — verify fix
- [ ] S3776: clean_manifest (16→15) — extract _clean_numbered_files
- [ ] S5145: remove filepath from log in collector.py _write_diff_parts + _write_parts
- [ ] S3776: _scan_one_directory (16→15) — extract _scan_directory_pattern
- [ ] S8502: set.update() instead of for+add in gatherer_query.py _find_importers
- [ ] S7504: document why list() is needed in watcher_diff.py _diff_files_sections
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
