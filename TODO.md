# TODO

## v4.3.0 — Architecture cleanup (details: llm_docs/specs/spec-v4.3.0-architecture-cleanup.md)
- [ ] Rename watch/ package to snapshot/ (~60 files)
- [ ] Deduplicate DiffSection: differ.py → api_types.py (~15 files)
- [ ] Clean up docstrings: remove version tags, standardize to one-line descriptions (~30 files)
- [ ] Clean up __all__ exports: narrow to intended public surface (~15 modules)
- [ ] Deduplicate split mode dispatch: document distinction, extract common constants

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
