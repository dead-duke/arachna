# TODO

## v4.2.1 — SonarCloud cleanup
- [ ] S3776: reduce cognitive complexity in _scan_directories (25→15), _build_parts_for_sections (18→15), _diff_files_sections (18→15)
- [ ] S2083: wrap remaining path constructions in validate_path (collector.py:105,228, atomic_write.py:34, presets.py:45)
- [ ] S5852: add _run_with_timeout to _C_LIKE_IMPORT_PATTERNS like _BLOCK_PATTERNS
- [ ] Deduplicate DiffSection: differ.py and api_types.py → use api_types everywhere
- [ ] Deduplicate split mode dispatch: _SPLIT_MODE_DISPATCH and _get_mode_strategies → single registry

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
