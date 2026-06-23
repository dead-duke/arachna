# TODO

## v5.3.0 — Audit resolution (20 findings)

- [ ] atomic_write.py:29,51 — narrow except Exception to (OSError, RuntimeError, ValueError) in both atomic_write_text and atomic_write_bytes
- [ ] atomic_write.py:29 — narrow except Exception in os.unlink cleanup path to (OSError, RuntimeError)
- [ ] differ_structural.py:122 — narrow except Exception to (ImportError, SyntaxError, OSError, RuntimeError, ValueError)
- [ ] language_dispatch.py:30 — narrow except Exception in _run_with_timeout to expected error types
- [ ] language_dispatch.py:30 — narrow bare except in thread function to specific exception types
- [ ] splitter.py — unify split implementations: remove _handle_oversized_in_build, use _pack_section_into_parts everywhere, command mode must split oversized sections with CONTINUES/CONTINUED markers instead of truncating
- [ ] gatherer_commands.py — migrate _collect_pre_commands, gather_files, _get_exclude_patterns_for_gather from profile: dict to ProfileConfig
- [ ] snapshot_diff_commands.py — migrate _collect_snapshot_pre_commands, _collect_snapshot_command, _build_pre_command_map, _build_current_pre_commands from profile: dict to ProfileConfig
- [ ] Remove 10 .to_dict() call sites after ProfileConfig migration across gatherer_commands and snapshot_diff_commands callers
- [ ] collector.py:280-296 — remove isinstance(profile, ProfileConfig) dict fallback, dead code after v5.2.0
- [ ] ARCHITECTURE.md — update "All lazy imports eliminated" to reflect reality: 36 lazy imports exist for optional deps, cyclic dependencies between packages eliminated
- [ ] PROJECT_MEMORY.md — update rule "ONLY main() may call Path.cwd()" to clarify: Path.cwd() allowed ONLY as default parameter value (root: Path | None = None), all callers must pass root explicitly
- [ ] snapshot_diff_files.py:180-192 — remove bare Path fallback in _read_file_from_disk, root=None is dead code
- [ ] compressor.py — remove estimate_savings from domain/__init__.py exports, unused in production
- [ ] gatherer_commands.py — remove gather_files from domain/__init__.py exports, unused in production
- [ ] gatherer_commands.py — remove gather_command from domain/__init__.py exports, unused in production
- [ ] domain/collection/__init__.py — remove 36 private symbols from __all__, keep only symbols imported from outside collection/
- [ ] snapshot/diff/__init__.py — remove 42 private symbols from __all__, keep only symbols imported from outside diff/
- [ ] domain/collection — replace print() warnings with logger.warning() in 10 places, keep print() only for stderr progress in _FullModeStrategy
- [ ] gatherer.py — add compress stats output to _assemble_command_content when verbose=True
- [ ] differ_structural.py — replace module-level threading.Lock for plugin check with @lru_cache on _check_plugins()
- [ ] store.py:_store_root — handle atomic_write_text fallback OSError explicitly instead of silent pass

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
