# TODO

## v1.4.4 — Security allowlist cleanup
- [x] Remove mkdir, xargs, sed, awk, tee from _ALLOWED_COMMANDS in runner.py
- [x] Update tests if any use removed commands
- [x] Bump version to 1.4.4 (__init__.py, pyproject.toml)
- [ ] Update CHANGELOG.md with v1.4.4 entry
- [ ] Publish v1.4.4 on PyPI

## Backlog
- [ ] Presets architecture refactor (split PRESETS dict into individual JSON files)
- [ ] Decompose collect() God function
- [ ] Remove _SERVICE_PRESETS hardcoded set
- [ ] LOW fixes: CHARS_PER_TOKEN dead code, unreachable return, double binary checks
- [ ] IDE integration (VS Code extension)
- [ ] Web UI for visual profile editor
