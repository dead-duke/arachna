# TODO

## v5.2.2 — SonarCloud + Audit: close all remaining findings

### S2083 — I/O on Path without visible validation (3 locations)
- [ ] path_utils.py: _check_toctou() returns SafePath, I/O methods use SafePath
- [ ] atomic_write.py: fallback path.write_text()/path.write_bytes() on SafePath
- [ ] store.py: verify SafePath.__truediv__ passes SonarCloud, add annotation if needed

### S8707 — Path constructed from user input without visible validation (2 locations)
- [ ] init.py: _validate_output_dir returns str, used inline in SafePath constructor
- [ ] atomic_write.py: remove to_path() from fallback, use SafePath directly

### S5713 — Redundant exception class
- [ ] presets_remote.py: remove urllib.error.URLError from except (caught by OSError)

### S5852 — Slow regex backtracking risk
- [ ] format_headers.py: split _RE_PY_IMPORT into _RE_PY_IMPORT_SIMPLE + _RE_PY_IMPORT_FROM

### Audit — Architecture
- [ ] domain/__init__.py: remove private symbols from __all__
- [ ] docs/ARCHITECTURE.md: fix "NO config/ imports" claim — api/ imports types from config/
- [ ] domain/interfaces.py: remove unused ObjectStore and ContentFormatter Protocols

### Audit — Code Quality
- [ ] domain/execution/__init__.py: remove unused _SPLITTER_C_LIKE_LANGS and _SPLITTER_SCRIPT_LANGS

### Verify
- [ ] 0 SonarCloud findings
- [ ] Audit report clean

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
