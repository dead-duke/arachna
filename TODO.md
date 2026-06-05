# TODO

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

