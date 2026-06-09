# TODO

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
