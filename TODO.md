# TODO

## v4.0.0 — Layered architecture (details: llm_docs/specs/spec-v4.0.0-layered-architecture.md)
- [ ] Create domain/ package: collector.py, gatherer.py, splitter.py, formatter.py, compressor.py, tokenizer.py, cache.py
- [ ] Create watch/ package: store.py, watcher.py, differ.py, differ_structural.py, store_errors.py
- [ ] Create plugins/ package: plugins.py
- [ ] Create api/ package: collect_api.py, watch.py, api_types.py, api_errors.py
- [ ] Create config/ package: config.py, presets.py, init.py, validator.py, doctor.py, hook.py, gitignore.py, completion.py
- [ ] Move interfaces.py to domain/interfaces.py, re-export from src/arachna/interfaces.py
- [ ] cli/ imports from domain/, watch/, plugins/, api/, config/ — explicit, no lazy imports
- [ ] Update all test imports for new module paths
- [ ] Remove proxy functions from __main__.py

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
