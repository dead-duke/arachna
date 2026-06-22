# TODO

## v5.2.2 — SonarCloud + Audit: close all remaining findings

### S2083 — I/O on Path without visible validation (3 locations)
- [x] path_utils.py: _check_toctou() returns SafePath, I/O methods use SafePath
- [x] atomic_write.py: fallback path.write_text()/path.write_bytes() on SafePath
- [x] store.py: explicit SafePath type annotations in rename_snapshot

### S8707 — Path constructed from user input without visible validation (2 locations)
- [x] init.py: _validate_output_dir returns str, used inline in SafePath constructor
- [x] atomic_write.py: fallback on SafePath instead of bare Path

### S5713 — Redundant exception class
- [x] presets_remote.py: remove urllib.error.URLError from except

### S5852 — Slow regex backtracking risk
- [x] format_headers.py: split _RE_PY_IMPORT into _RE_PY_IMPORT_SIMPLE + _RE_PY_IMPORT_FROM

### Audit — Architecture
- [x] domain/__init__.py: remove private symbols from __all__
- [x] docs/ARCHITECTURE.md: fix api/config imports claim
- [x] domain/interfaces.py: remove unused ObjectStore and ContentFormatter Protocols

### Audit — Code Quality
- [x] domain/execution/__init__.py: remove unused _SPLITTER_C_LIKE_LANGS and _SPLITTER_SCRIPT_LANGS

### Verify
- [ ] 0 SonarCloud findings
- [ ] Audit report clean

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
