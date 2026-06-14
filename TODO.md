# TODO

## v3.5.0 — Ecosystem: testability, CI, docs, security, man page (details: llm_docs/specs/spec-v3.5.0-ecosystem.md)
- [ ] Replace monkeypatch.chdir with explicit root/output_dir params — start with config.py, store.py, then gatherer.py, collector.py (module by module)
- [ ] Remove 9 importlib.reload calls — inject config via parameters instead of os.environ at import time
- [ ] Integrate benchmarks into CI with pytest --benchmark-compare for regression detection
- [ ] Add throughput, cold start, large file regression checks to baseline
- [ ] Document pre_commands threat model in README Security section
- [ ] Add presets schema validation for presets update — validate structure before merge
- [ ] Extract ADR from PROJECT_MEMORY.md into docs/adr/ with dates and statuses (proposed/accepted/deprecated)
- [ ] Add Security section to README with threat model and two-level sandbox documentation
- [ ] Create arachna.1 man page installed with pip
- [ ] Add try-except with warning for pre_commands failures — log warning, don't fail the pipeline
- [ ] Add Strategy pattern for mode dispatch in _assemble_file_content — replace if-elif chain with ModeStrategy classes
- [ ] Set up pdoc API reference on GitHub Pages with CI deploy

## v3.6.0 — Data pipeline: manifest API + metrics + performance (details: llm_docs/specs/spec-v3.6.0-data-pipeline.md)
- [ ] Add arachna manifest --json command — machine-readable manifest with content hashes and part dependencies
- [ ] Add CollectResult.metrics field — extract/transform/load breakdown in public API
- [ ] Write .arachna_metrics.json alongside manifest — pipeline observability for CLI users
- [ ] Add ThreadPoolExecutor for parallel file reading + formatting in _stream_full_mode (I/O-bound, GIL-safe)
- [ ] Add streaming=True flag to compute_diff — read files from store one-by-one, not all at once
- [ ] Add manifest command tests
- [ ] Add parallel collect benchmarks (threaded vs sequential)

## v4.0.0 — Layered architecture (details: llm_docs/specs/spec-v4.0.0-layered-architecture.md)
- [ ] Split flat 26 modules into packages: cli/, domain/, watch/, plugins/, api/, config/
- [ ] Move domain modules: collector.py, gatherer.py, splitter.py, formatter.py, compressor.py, tokenizer.py, cache.py
- [ ] Move watch modules: store.py, watcher.py, differ.py, differ_structural.py, store_errors.py
- [ ] Move api modules: collect_api.py, watch.py, api_types.py, api_errors.py
- [ ] Move config modules: config.py, presets.py, init.py, validator.py, doctor.py, hook.py, gitignore.py, completion.py
- [ ] Update all internal imports — no lazy imports needed, clean dependency graph
- [ ] Update all tests for new module paths
- [ ] Remove proxy functions from __main__.py (backward compat period ended)

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
