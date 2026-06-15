# TODO

## v4.0.0 — Layered architecture (details: llm_docs/specs/spec-v4.0.0-layered-architecture.md)
- [x] Create domain/ package: collector.py, gatherer.py, splitter.py, formatter.py, compressor.py, tokenizer.py, cache.py
- [x] Create watch/ package: store.py, watcher.py, differ.py, differ_structural.py, store_errors.py
- [x] Create plugins/ package: plugins.py
- [x] Create api/ package: collect_api.py, watch.py, api_types.py, api_errors.py
- [x] Create config/ package: config.py, presets.py, init.py, validator.py, doctor.py, hook.py, gitignore.py, completion.py
- [x] Move interfaces.py to domain/interfaces.py, re-export from src/arachna/interfaces.py
- [x] cli/ imports from domain/, watch/, plugins/, api/, config/ — explicit, no lazy imports
- [x] Update all test imports for new module paths
- [x] Remove proxy functions from __main__.py
- [x] Remove _import_graph_cache global — encapsulate into gatherer strategy
- [x] Lazy-init _MODE_STRATEGIES instead of import-time instantiation
- [x] _make_profile deduplication — consolidated into tests/conftest.py
- [x] Mark spec-v3.6.0-data-pipeline.md checkboxes as done

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
