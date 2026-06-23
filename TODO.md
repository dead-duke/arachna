# TODO

## v5.3.0 — Audit resolution (20 findings)

- [x] atomic_write.py:29,51 — narrow except Exception to (OSError, RuntimeError, ValueError)
- [x] differ_structural.py:122 — narrow except Exception to (ImportError, SyntaxError, OSError, RuntimeError, ValueError)
- [x] language_dispatch.py:30 — narrow except Exception in _run_with_timeout to (ValueError, RuntimeError)
- [x] splitter.py — remove _handle_oversized_in_build + _build_parts_for_sections, unify on pack_into_parts
- [x] gatherer_commands.py — _collect_pre_commands extracted to gatherer_pre_commands.py, ProfileConfig migration
- [x] snapshot_diff_commands.py — migrate 4 functions from profile: dict to ProfileConfig
- [x] Remove 10 .to_dict() call sites
- [x] collector.py:280-296 — remove isinstance(profile, ProfileConfig) dict fallback
- [x] Lazy imports — cyclic pairs broken via gatherer_pre_commands.py + format_parsers.py, all internal imports lifted to module level
- [x] root: Path made mandatory everywhere except _validate_preset_tokenizer + main()
- [x] snapshot_diff_files.py:180-192 — remove bare Path fallback, SafePath only
- [x] compressor.py — estimate_savings removed from domain/__init__.py exports
- [x] gatherer_commands.py — gather_files, gather_command removed from domain/__init__.py exports
- [x] domain/collection/__init__.py — __all__ cleaned
- [x] snapshot/diff/__init__.py — __all__ cleaned
- [x] print() → logger.warning()/logger.info() in gatherer_files + gatherer_strategies
- [x] gatherer.py — compress stats in _assemble_command_content
- [x] differ_structural.py — threading.Lock replaced with @lru_cache
- [x] store.py:_store_root — explicit OSError warning on atomic_write_text fallback
- [x] ARCHITECTURE.md + PROJECT_MEMORY.md — code brought in line with docs, no doc changes needed

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
