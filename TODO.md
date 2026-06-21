# TODO

## v5.2.0 — Code quality + architecture fixes
- [x] Break api/ ↔ config/ cycle
- [x] Move compute_diff_stats to domain/differ_stats.py
- [x] SafeLogger: _sanitize_log()
- [x] Dataclass config: ProfileConfig + ArachnaConfig
- [x] Enum/Literal: CollectionMode, OutputFormat, SplitMode
- [x] time.sleep → os.utime in tests
- [x] mock_popen → tests/conftest.py
- [x] Empty conftest.py → __init__.py
- [x] Reorganize domain/ into 5 subpackages
- [x] Reorganize snapshot/ into 3 subpackages
- [x] Reorganize config/ into 3 subpackages
- [x] Mirror restructure in tests/

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
