# TODO

## v5.1.0 — SafePath + Audit fixes (details: llm_docs/specs/spec-v5.1.0-safepath.md)
- [x] MEDIUM: Narrow except Exception to except OSError in atomic_write.py, cache.py, hook.py, snapshot_diff.py
- [x] HIGH: Fix api/snapshot.py importing private _functions from snapshot_diff — make public or wrap
- [x] CRITICAL: Remove importlib.import_module fallback in tokenizer.py — only local files + known-safe tokenizers
- [x] SafePath: Create class in domain/path_utils.py
- [x] SafePath: Refactor collector.py, store.py, snapshot_diff.py, init.py, presets.py, cli/*.py
- [x] MEDIUM: Decompose snapshot/snapshot_diff.py (720 lines) — extract snapshot_diff_files, snapshot_diff_commands, snapshot_diff_repo_map
- [x] MEDIUM: Decompose domain/formatter.py (605 lines) — extract format_language, format_binary, format_headers, format_output, format_exclude
- [x] LOW: Atomic writes in config/init.py, cli/presets.py, cli/_helpers.py — use atomic_write_text
- [x] LOW: Count KeyError as error in _cmd_collect_validate — don't silently exclude broken profiles
- [x] LOW: Elevate DANGEROUS command log from logger.warning to logger.error
- [x] LOW: Replace module-level _log_writer with parameter injection in runner.py
- [x] LOW: Wrap _builtin_cache and _MODE_STRATEGIES in threading.Lock for thread safety
- [x] LOW: Wrap plugin flags (_HAS_TS, _HAS_TIKTOKEN, etc.) in threading.Lock for thread safety
- [x] LOW: Replace importlib.reload in tests with @lru_cache factory functions
- [x] Fix S1481: unused tokens_by_file in cli/collect.py
- [x] Fix S2737: comment in collector.py empty except
- [x] Fix S7504: document list() in snapshot_diff.py
- [x] Unit tests for SafePath (14 tests)
- [x] All tests pass, make check clean, 0 SonarCloud findings

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
