# TODO

## v5.2.0 — Code quality + architecture fixes (details: llm_docs/specs/spec-v5.2.0-code-quality-architecture.md)
- [ ] Break api/ ↔ config/ cycle — api accepts config as parameter, config/remote uses domain/ directly
- [ ] Move compute_diff_stats from snapshot/differ.py to domain/differ_stats.py
- [ ] SafeLogger: Centralize CRLF sanitization with _sanitize_log() helper
- [ ] Dataclass-based config: ProfileConfig + ArachnaConfig with __post_init__ validation
- [ ] Enum/Literal for modes: CollectionMode, OutputFormat, SplitMode
- [ ] Replace time.sleep with os.utime in incremental cache tests
- [ ] Move mock_popen from tests/domain/conftest.py to tests/conftest.py
- [ ] Replace empty conftest.py files with __init__.py
- [ ] Reorganize domain/ into 5 subpackages: cache, collection, formatting, tokenization, execution
- [ ] Reorganize snapshot/ into 3 subpackages: store, diff, rename
- [ ] Reorganize config/ into 3 subpackages: core, presets, setup
- [ ] Mirror restructure in tests/

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
