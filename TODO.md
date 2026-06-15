# TODO

## v3.6.0 — Data pipeline: manifest API + metrics + performance (details: llm_docs/specs/spec-v3.6.0-data-pipeline.md)
- [ ] Add arachna manifest command with --json flag
- [ ] manifest --json output: {project_name, profiles, parts: [{file, tokens, hash, dependencies}]}
- [ ] collect() writes .arachna_metrics.json: extract_time_ms, transform_time_ms, load_time_ms, files_read, files_skipped, tokens_raw, tokens_compressed, compression_ratio
- [ ] CollectResult.metrics: PipelineMetrics | None in collect_api.py
- [ ] Add PipelineMetrics dataclass to api_types.py
- [ ] ThreadPoolExecutor for parallel file reading + formatting in _stream_full_mode (ARACHNA_MAX_WORKERS env, default 4)
- [ ] compute_diff streaming=True parameter — read files from store one-by-one
- [ ] max_tokens=0 unlimited mode — config.py, validator, splitter, gatherer
- [ ] Progress output to stderr: file count every 100 files when verbose
- [ ] Unit tests for all new features
- [ ] Benchmark: parallel vs sequential collect on 1000 files

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
