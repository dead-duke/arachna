# TODO

## v1.8.0 — Headers, --query, repo-map mode (details: llm_docs/specs/spec-v1.8.0-headers-query-repo-map.md)
- [x] formatter.py: _generate_header — extract imports, exports from file (Python: ast, C-like: regex, fallback: empty)
- [x] gatherer.py: _filter_by_query — keyword match + import chain analysis
- [x] gatherer.py: _collect_import_graph — build {file: [imports]} dict from headers
- [x] __main__.py: --query "fix authentication bug" flag for filtering
- [x] __main__.py: --mode repo-map (signatures only, no bodies)
- [x] __main__.py: --mode headers (full code + headers, auto-enabled with --query)
- [x] splitter.py: _extract_signatures — strip function/class bodies, keep signatures
- [x] Tests: headers for Python/JavaScript/unknown, query filtering, repo-map for Python/C-like/unknown, --mode flags

## v2.0.0 — Agent API + structural diff (details: llm_docs/specs/spec-v2.0.0-agent-api.md)
- [ ] Create watch.py with public API functions (create_snapshot, list_snapshots, update_snapshot, delete_snapshot, snapshot_info)
- [ ] Create watch_types.py with dataclasses (SnapshotInfo, DiffStats, DiffSection, DiffResult, CollectResult, StoreStats, GCResult)
- [ ] Create watch_errors.py with exception classes (ArachnaError, SnapshotNotFoundError, SnapshotExistsError, ProfileNotFoundError)
- [ ] Implement structural diff via differ_structural.py (ast for Python, regex for C-like, fallback difflib)
- [ ] Add --mode structural flag to --diff CLI
- [ ] Unit tests for all public API functions
- [ ] Integration tests for agent workflow (Delirium-style)

## Backlog
- [ ] Man page (arachna.1) installed with pip
- [ ] Add more language presets: Go, Rust, Zig, Lua, Elixir, Haskell, Gleam
- [ ] Lazy loading for presets (deferred — low priority)
