# TODO

## v4.1.1 — Quick fixes from audit
- [ ] _find_query_candidate: pass root parameter from run_benchmark (profiler.py)
- [ ] completion.py: update to argparse subparsers (collect, snapshot, diff, etc.)
- [ ] is_excluded: support ** glob patterns — fnmatch limitation requires * prefix workaround
- [ ] remote: true profile field — explicit marker for remote collection profiles
- [ ] Strict --profile for --repo: exact match or error (no silent fallback)
- [ ] Auto-selection: one remote profile → use it, multiple → error with names, none → auto-detect
- [ ] ValueError with available profile names when ambiguous or missing
- [ ] Deduplicate literals: "Output directory" × 4 (__main__.py), "pre: " × 3 (gatherer_query.py), "__init__.py" × 4 (tokenizer.py), "sha256:" × 3 (store.py), "command output" × 3 (watcher.py)
- [ ] Remove unused params: root (diff.py:128), snapshot_id+to_snapshot_id (collector.py:218-219), query+mode (gatherer.py:29), path (watcher.py:133), fmt (watcher.py:165), streaming (watcher.py:568), profile (watcher.py:605), lang (watcher.py:692+722)
- [ ] runner.py:313 — fill empty pass block in dry_run
- [ ] differ_structural.py:189,244,247 — startswith("class ") or startswith("interface ") → startswith(("class ", "interface "))
- [ ] store.py:53 — write_object invert condition for single return
- [ ] Fix unused variables: tokens_by_file→_ (collect.py:57, diff.py:51), created_d→_ (benchmarks.py:72)
- [ ] watcher.py:179,259 — remove unnecessary list() call
- [ ] watcher.py:228,230 — for+add() → set.update()
- [ ] collector.py:53 — fill empty except ImportError for msvcrt
- [ ] runner.py:276 — remove redundant except Exception after except OSError

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
