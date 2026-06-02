# TODO

## v1.5.1 — Remaining LOW fixes from audit + v1.5.0 review
- [x] Simplify _collect_named_sections() pass-through in gatherer.py
- [x] Replace if-elif chain in main() with dispatch dict
- [x] Sync DEFAULT_EXCLUDE with gitignore.py patterns
- [x] Cache arachna --list output for shell completion
- [x] Replace monkeypatch.chdir with absolute paths in test_cache.py
- [x] Fix fragile mock target in test_post_commands_executed
- [x] Remove unused service field from preset JSON files
- [x] Deduplicate _TEXT_EXTENSIONS and _EXT_LANG in formatter.py
- [x] Remove redundant mkdir in merge mode in collector.py
- [x] Bump version to 1.5.1
- [x] Update CHANGELOG.md
- [x] Update TEST_REPORT.md
- [ ] Publish v1.5.1 on PyPI

## Backlog
- [ ] Add more language presets (Go, Rust, Zig, Lua, etc.)

