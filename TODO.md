# TODO

## v2.9.2 — Zero-dep fixes (details: llm_docs/specs/spec-v2.9.2-zero-dep-fixes.md)
- [x] Fix: collect_api double I/O — return parts from memory, add write_to_disk=False param
- [x] Fix: TOC substring matching — split_sections returns indices relative to original input list, not filtered
- [x] Fix: config inheritance — add "extends" field (scalars override, exclude lists append, source lists override)
- [x] Fix: config inheritance UX — warning on field conflicts between parent and child
- [x] Fix: snapshot paths — store relative paths from project root, handle find_config()==None fallback
- [x] Fix: max_output_size in sandbox — Popen with binary stdout, chunked read, decode at end, truncation marker in output
- [x] Fix: chars_per_token in profile — replace hardcoded 4 with configurable value
- [x] Fix: run_command always returns str with truncation marker, not a tuple
- [x] Fix: update all internal callers of collector.collect() for new 3-tuple return (files, tokens, parts)
- [x] Fix: streaming for full mode — stat+estimate tokens, pack, then stream content. Repo-map/headers stay in-memory (need parsing)
- [ ] Doc: add "Known limitations" section to README (structural diff needs plugins, incremental in CI, config inheritance semantics)
- [ ] Doc: ARCHITECTURE.md data flow diagrams, module responsibilities, extension points
- [x] Benchmark: simple performance test — collect 1000 files baseline, save to docs/BENCHMARKS.md
- [x] Test: streaming pipeline — test_streaming_1000_files_no_oom
- [x] Test: streaming repo-map — test_streaming_repo_map_stays_in_memory
- [x] Test: config inheritance — test_config_extends_scalar, test_config_extends_exclude_append, test_config_extends_source_override, test_config_extends_circular
- [x] Test: max_output_size — test_max_output_size_truncation, test_max_output_size_within_limit
- [x] Test: snapshot relative paths — test_snapshot_relative_paths
- [x] Test: collect_api write_to_disk — test_collect_api_write_to_disk_false, test_collect_api_parts_match_files
- [x] LOW TEST-01: runner.py shell=True not verified — add assert_called_with(shell=True)
- [x] LOW TEST-02: watcher.py _diff_file_sets isolated unit tests
- [x] LOW TEST-03: gatherer.py _collect_import_graph edge case tests
- [x] LOW TEST-04: splitter.py binary search custom tokenizer tests
- [x] LOW TEST-05: presets.py fetch_presets timeout test
- [x] LOW: gatherer.py include_header naming — document behavior clearly
- [x] LOW: watcher.py isolated tests — add unit tests for helper functions
- [x] LOW: presets.py timeout not tested — add slow network mock test
- [x] LOW: gatherer.py _collect_import_graph caching — cache per file list
- [x] LOW: formatter.py _is_binary_allowed — add direct unit tests
- [x] LOW: cache.py SHA256 fallback path — add explicit test for mtime within tolerance + size differs
- [ ] Version bump: __init__.py → 2.9.2
- [ ] Version bump: pyproject.toml → 2.9.2
- [ ] Update TEST_REPORT.md with new test counts
- [ ] Update CHANGELOG for v2.9.2

## v3.0 — CLI redesign (details: llm_docs/specs/spec-v3.0-plugins-cli.md)
- [ ] CLI: argparse subparsers — arachna collect/snapshot/diff/store/plugins/presets/completion
- [ ] CLI: remove all manual sys.argv parsing, delete cli_watch.py
- [ ] CLI: update Makefile targets — arachna --snapshot create → arachna snapshot create, etc.
- [ ] Doc: update README examples — arachna --profile code → arachna collect --profile code, etc.
- [ ] Test: CLI subparsers — test_cli_subparser_help_collect, test_cli_subparser_help_snapshot, test_cli_subparser_help_diff
- [ ] Test: CLI subparsers — test_cli_collect_profile, test_cli_collect_all, test_cli_collect_clean, test_cli_collect_list
- [ ] Version bump: __init__.py → 3.0.0
- [ ] Version bump: pyproject.toml → 3.0.0
- [ ] Update TEST_REPORT.md with new test counts
- [ ] Update CHANGELOG for v3.0

## v3.1 — Plugin system (details: llm_docs/specs/spec-v3.1-plugins.md)
- [ ] Plugin system: environment detector (pipx, poetry, uv, conda, venv, system, PEP 668)
- [ ] Plugin system: install_command — pip/python extras integration, user-friendly messages
- [ ] Plugin system: lazy import with fallback to text diff for uninstalled plugins
- [ ] Plugin: tree-sitter structural diff for JavaScript, TypeScript, Go
- [ ] Plugin: tiktoken/transformers via plugin interface
- [ ] Fix: pin tree-sitter~=0.21.0 in pyproject.toml extras
- [ ] pyproject.toml: per-language extras (arachna[javascript], arachna[go], etc.)
- [ ] arachna plugins list/install/uninstall commands
- [ ] Test: environment detector — test_detect_environment_pipx, test_detect_environment_poetry, test_detect_environment_venv, test_detect_environment_system
- [ ] Test: lazy import — test_lazy_import_fallback_js, test_lazy_import_success_js
- [ ] Test: plugin install — test_plugin_install_command_pipx, test_plugin_install_command_venv, test_plugin_install_command_pep668
- [ ] Version bump: __init__.py → 3.1.0
- [ ] Version bump: pyproject.toml → 3.1.0
- [ ] Update TEST_REPORT.md with new test counts
- [ ] Update CHANGELOG for v3.1

## v3.2 — Benchmarking + Integration examples
- [ ] Add arachna --benchmark command — measure token savings and time across modes
- [ ] Integration example: LangGraph multi-agent workflow with programmer + tester agents
- [ ] Integration example: CrewAI agent pipeline
- [ ] Integration example: AutoGen agent loop
- [ ] README: explicit "Business model — free software, no SaaS" section
- [ ] Version bump: __init__.py → 3.2.0
- [ ] Version bump: pyproject.toml → 3.2.0
- [ ] Update TEST_REPORT.md with new test counts
- [ ] Update CHANGELOG for v3.2
