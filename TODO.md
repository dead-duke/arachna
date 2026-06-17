# TODO

## v4.1.1 — Quick fixes from audit
- [x] runner.py:276 — remove redundant except Exception after except OSError
- [x] runner.py:313 — fill empty pass block in dry_run
- [x] collector.py:53 — fill empty except ImportError for msvcrt
- [x] store.py:53 — write_object invert condition for single return
- [x] differ_structural.py:189,244,247 — startswith(("class ", "interface "))
- [x] Fix unused variables: tokens_by_file→_ (collect.py:57, diff.py:51), created_d→_ (benchmarks.py:72)
- [x] watcher.py:179,259 — remove unnecessary list() call
- [x] watcher.py:228,230 — for+add() → set.update()
- [x] Remove unused params: root, snapshot_id, to_snapshot_id, query, mode, path, streaming, profile, lang
- [x] Deduplicate literals: _OUTPUT_DIR_HELP, _PRE_LABEL_PREFIX, _INIT_FILE, _SHA256_PREFIX, _COMMAND_OUTPUT_LABEL
- [x] _find_query_candidate: pass root parameter from run_benchmark
- [x] completion.py: update to argparse subparsers
- [x] is_excluded: support directory-scoped patterns
- [x] remote: true profile field
- [x] Strict --profile for --repo: exact match or error
- [x] Auto-selection: one remote → use, multiple → error, none → auto-detect
- [x] ValueError with available profile names

## v4.2.0 — Code quality
- [ ] Wrap _collect_parallel params in dataclass (14 → 1 object)
- [ ] Move domain/remote.py → config/ or cli/ (layer violation)
- [ ] Simplify _BLOCK_PATTERNS: (?P<name>...) → (...), m.group("name") → m.group(1)
- [ ] Replace similarity == 1.0 with math.isclose() in rename detection tests
- [ ] Replace _RE_TRAILING_WS regex with str.rstrip() in compressor.py
- [ ] Break _RE_C_LIKE_IMPORT into chain of single-purpose patterns (like _BLOCK_PATTERNS)
- [ ] Split gatherer_core.py: gatherer_files.py + gatherer_commands.py
- [ ] Split watcher.py: watcher_diff.py + watcher_rename.py
- [ ] Split presets.py: presets_remote.py (fetch_presets + merge_presets)
- [ ] Add _validate_path() helper for SonarCloud S2083 (path injection false positives → explicit validation)
- [ ] Reduce cognitive complexity: splitter.py (3 functions), runner.py (3 functions), watcher.py (7 functions), formatter.py (2 functions), gitignore.py (1 function), gatherer_strategies.py (1 function), language_dispatch.py (1 function), gatherer_query.py (2 functions), tokenizer.py (1 function), store.py (2 functions), differ_structural.py (2 functions), collector.py (1 function), gatherer_core.py (1 function), renderer.py (1 function), doctor.py (1 function), init.py (1 function), profiler.py (1 function), manifest.py (1 function), diff.py (1 function), collect.py (2 functions)
- [ ] diff --line-numbers: show line numbers in REMOVED/ADDED blocks from snapshot file positions

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
