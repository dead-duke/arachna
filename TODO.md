# TODO

## v1.7.0 — Watch Advanced: cross-snapshot diff, rename/move detection, grouped output

### store.py
- [x] add rename_snapshot(old_id, new_id) method
- [x] update manifest id/name, update HEAD if needed
- [x] raise error on duplicate name

### differ.py
- [x] add similarity field to DiffSection (float 0.0-1.0)
- [x] add renamed and moved counts to compute_diff_stats

### watcher.py — cross-snapshot diff
- [x] add to_snapshot_id parameter to compute_diff (optional, default None)
- [x] cross-snapshot mode: load both manifests from store, compare hashes
- [x] cross-snapshot mode: read old content from store, new content from store

### watcher.py — rename/move detection
- [x] detect exact rename: same hash, different filename
- [x] detect exact move: same hash, different directory
- [x] detect rename+move: same hash, different name AND directory
- [x] detect similar rename: SequenceMatcher > 0.7 + different filename
- [x] detect similar move: SequenceMatcher > 0.7 + different directory
- [x] edge cases: multiple files with same hash, binary files, dissimilar (<=0.7)

### watcher.py — grouped output
- [ ] group DiffSections by type: renamed, moved, modified, added, deleted
- [ ] generate summary header with counts
- [ ] flat mode via --diff --flat for backward compatibility

### __main__.py
- [ ] --diff --to <id> flag for cross-snapshot diff
- [ ] --snapshot info <id> subcommand
- [ ] --snapshot info <id> --profile
- [ ] --snapshot info <id> --stats
- [ ] --snapshot rename <old> <new> subcommand
- [ ] --snapshot list: remove duplicate id/name column
- [ ] --diff --flat flag (backward compatible, current behaviour)
- [ ] --diff grouped output as default

## v1.8.0 — Headers, --query, repo-map mode (see llm_docs/spec-v1.8.0-headers-query-repo-map.md)

## v2.0.0 — Agent API + structural diff (see llm_docs/spec-v2.0.0-agent-api.md)

## Backlog
- [ ] Man page (arachna.1) installed with pip
- [ ] Add more language presets: Go, Rust, Zig, Lua, Elixir, Haskell, Gleam
- [ ] Lazy loading for presets (deferred — low priority)
