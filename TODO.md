# TODO

## v1.5.2 — Race condition fix + escaped pipes
- [x] File locking in _find_next_part_num() for concurrent merge safety
- [x] Handle escaped pipes (\|) in _split_pipe_parts()
- [ ] Bump version to 1.5.2
- [ ] Update CHANGELOG.md
- [ ] Update TEST_REPORT.md
- [ ] Publish v1.5.2 on PyPI

## v1.5.3 — Incremental mode optimization
- [ ] Replace mtime-only check with mtime_ns + st_size pre-check
- [ ] Add SHA256 fallback when size/mtime changed (smart hybrid)
- [ ] Handle false positives: git checkout updates mtime, SHA256 confirms unchanged
- [ ] Store mtime_ns, st_size, sha256 in cache
- [ ] Bump version to 1.5.3
- [ ] Update CHANGELOG.md
- [ ] Update TEST_REPORT.md
- [ ] Publish v1.5.3 on PyPI

## Backlog
- [ ] v1.6.0 — Watch MVP: store.py, differ.py, watcher.py, --snapshot, --diff
- [ ] v1.6.1 — Watch polish: --diff --full, --store gc/stats, XML format
- [ ] v1.7.0 — Named snapshots, cross-snapshot diff, rename detection
- [ ] v2.0.0 — Agent API, Delirium integration
- [ ] Man page (arachna.1) installed with pip
- [ ] Add more language presets (Go, Rust, Zig, Lua, etc.)
- [ ] Lazy loading for presets
