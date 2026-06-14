# TODO

## v3.5.0 — Ecosystem: testability, CI, docs, security, man page
- [x] find_config(root), load_config(root)
- [x] store/gatherer/collector tests: 0 monkeypatch.chdir
- [x] runner.py: run_pre_commands try-except, max_output_size parameter
- [x] tokenizer.py: lazy plugins, _SAFE_TOKENIZERS/_DEFAULT_CHARS_PER_TOKEN via functions
- [x] presets.py: fetch_presets(timeout), _validate_preset schema validation
- [x] gatherer.py: Strategy pattern + root chain
- [x] collector.py: collect(root)
- [x] importlib.reload: 2/4 fixed, 2 system mocks remain
- [ ] CI benchmarks
- [ ] README Security section
- [ ] ADR extraction
- [ ] arachna.1 man page
- [ ] pdoc CI deploy

## v3.6.0 — Data pipeline: manifest API + metrics + performance
- [ ] arachna manifest --json
- [ ] CollectResult.metrics
- [ ] .arachna_metrics.json
- [ ] ThreadPoolExecutor parallel I/O
- [ ] compute_diff streaming=True

## v4.0.0 — Layered architecture
- [ ] Split modules into packages

## Backlog
- [ ] Integration examples: LangGraph, CrewAI, AutoGen
