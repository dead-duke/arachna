# TODO

## v5.1.0 — SafePath + Audit fixes (details: llm_docs/specs/spec-v5.1.0-safepath.md)
- [ ] CRITICAL: Remove importlib.import_module fallback in tokenizer.py — only local files + known-safe tokenizers
- [ ] HIGH: Fix api/snapshot.py importing private _functions from snapshot_diff — make public or wrap
- [ ] SafePath: Create class in domain/path_utils.py, refactor all I/O modules
- [ ] SafePath: Refactor collector.py, store.py, snapshot_diff.py, init.py, presets.py, cli/*.py
- [ ] MEDIUM: Decompose snapshot/snapshot_diff.py (720 lines) — extract snapshot_diff_files, snapshot_diff_commands, snapshot_diff_repo_map
- [ ] MEDIUM: Decompose domain/formatter.py (605 lines) — extract format_language, format_binary, format_headers, format_output, format_exclude
- [ ] MEDIUM: Narrow except Exception to except OSError in atomic_write.py, cache.py, hook.py, snapshot_diff.py
- [ ] LOW: Atomic writes in config/init.py, cli/presets.py, cli/_helpers.py — use atomic_write_text
- [ ] LOW: Count KeyError as error in _cmd_collect_validate — don't silently exclude broken profiles
- [ ] LOW: Elevate DANGEROUS command log from logger.warning to logger.error
- [ ] LOW: Replace module-level _log_writer with parameter injection in runner.py
- [ ] LOW: Wrap _builtin_cache and _MODE_STRATEGIES in threading.Lock for thread safety
- [ ] LOW: Wrap plugin flags (_HAS_TS, _HAS_TIKTOKEN, etc.) in threading.Lock for thread safety
- [ ] LOW: Replace importlib.reload in tests with @lru_cache factory functions
- [ ] Fix S1481: unused tokens_by_file in cli/collect.py
- [ ] Fix S2737: comment in collector.py empty except
- [ ] Fix S7504: document list() in snapshot_diff.py
- [ ] Unit tests for SafePath
- [ ] All tests pass, make check clean, 0 SonarCloud findings

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
