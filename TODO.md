# TODO

## v5.2.1 — SonarCloud + Audit fixes (details: llm_docs/specs/spec-v5.2.1-sonarcloud-audit-fixes.md)
- [x] HIGH: Remove unused config param from api/snapshot.py (S1172 x3)
- [x] HIGH: Fix broken import in examples/delirium_agent.py
- [x] MEDIUM: Deduplicate _dict_to_profile — add ProfileConfig.from_dict(), replace 5 copies
- [x] MEDIUM: S5852 — refactor _RE_PY_MULTILINE_IMPORT, _RE_ES6_IMPORT_FROM, _RE_COMMONJS_REQUIRE
- [x] MEDIUM: S2083 — atomic_write.py accept SafePath, explicit validate_path() before I/O
- [x] MEDIUM: S2083 — path_utils.py _check_toctou() returns resolved path
- [x] MEDIUM: S2083 — store.py split json.loads(sp.read_text()) into two lines
- [x] MEDIUM: S2083 — init.py _write_config passes SafePath directly
- [x] MEDIUM: Document shell=True limitations in SECURITY.md + add adversarial pre_commands tests
- [x] MEDIUM: Remove backward-compat — delete snapshot/snapshots.py, arachna/interfaces.py
- [x] MEDIUM: Remove dict branch from get_root() — ArachnaConfig only, fix all test callers
- [x] MEDIUM: Add Protocol types to function signatures (Tokenizer, ObjectStore, ContentFormatter)
- [x] MEDIUM: Replace global state with factory functions (gatherer_strategies, tokenizer, presets)
- [x] LOW: Bare except → specific exceptions in cli/snapshot.py, cli/collect.py, presets_remote.py
- [x] LOW: Remove dead if __name__ block in config/completion.py
- [x] LOW: merge_lock — add PID to lock file, check stale lock before blocking
- [x] Tests: Update all imports + callers + dict→ArachnaConfig, regression 1640 tests pass

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
