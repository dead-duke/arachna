# TODO

## v1.5.2 — Race condition fix + escaped pipes
- [ ] Add file locking to _find_next_part_num() for concurrent merge safety
- [ ] Handle escaped pipes (\|) in _split_pipe_parts()
- [ ] Bump version to 1.5.2 (__init__.py, pyproject.toml)
- [ ] Update CHANGELOG.md with v1.5.2 entry
- [ ] Update TEST_REPORT.md
- [ ] Publish v1.5.2 on PyPI

## Backlog
- [ ] Add more language presets (Go, Rust, Zig, Lua, etc.)
- [ ] Lazy loading for presets (load only needed JSON files)
