# TODO

## v1.5.0 — Architecture refactor + LOW fixes
- [x] Presets architecture refactor — split PRESETS dict into individual JSON files
- [x] Remove _SERVICE_PRESETS hardcoded set
- [x] Decompose collect() God function
- [x] Remove CHARS_PER_TOKEN dead code from splitter.py
- [x] Remove unreachable return after sys.exit in _run_profile()
- [x] Remove double binary extension checks in formatter.py
- [x] Remove redundant mkdir in merge mode in collector.py
- [x] Bump version to 1.5.0 (__init__.py, pyproject.toml)
- [ ] Update CHANGELOG.md with v1.5.0 entry
- [ ] Update TEST_REPORT.md
- [ ] Publish v1.5.0 on PyPI

## Backlog
- [ ] IDE integration (VS Code extension)
- [ ] Web UI for visual profile editor
