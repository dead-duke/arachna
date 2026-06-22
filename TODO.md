# TODO

## v5.2.1 — SonarCloud + Audit fixes (details: llm_docs/specs/spec-v5.2.1-sonarcloud-audit-fixes.md)
- [ ] HIGH: Remove unused config param from api/snapshot.py (S1172 x3)
- [ ] HIGH: Fix broken import in examples/delirium_agent.py
- [ ] MEDIUM: Deduplicate _dict_to_profile — add ProfileConfig.from_dict(), replace 5 copies
- [ ] MEDIUM: S5852 — refactor _RE_PY_MULTILINE_IMPORT, _RE_ES6_IMPORT_FROM, _RE_COMMONJS_REQUIRE
- [ ] MEDIUM: S2083 — atomic_write.py accept SafePath, explicit validate_path() before I/O
- [ ] MEDIUM: S2083 — path_utils.py _check_toctou() returns resolved path
- [ ] MEDIUM: S2083 — store.py split json.loads(sp.read_text()) into two lines
- [ ] MEDIUM: S2083 — init.py _write_config passes SafePath directly
- [ ] MEDIUM: Document shell=True limitations in SECURITY.md + add adversarial pre_commands tests
- [ ] MEDIUM: Remove backward-compat — delete snapshot/snapshots.py, arachna/interfaces.py
- [ ] MEDIUM: Remove dict branch from get_root() — ArachnaConfig only, fix all test callers
- [ ] MEDIUM: Add Protocol types to function signatures (Tokenizer, ObjectStore, ContentFormatter)
- [ ] MEDIUM: Replace global state with factory functions (gatherer_strategies, tokenizer, presets)
- [ ] LOW: Bare except → specific exceptions in cli/snapshot.py, cli/collect.py, presets_remote.py
- [ ] LOW: Remove dead if __name__ block in config/completion.py
- [ ] LOW: merge_lock — add PID to lock file, check stale lock before blocking
- [ ] Tests: Update all imports + callers + dict→ArachnaConfig, regression 1641 tests pass

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
