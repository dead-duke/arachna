# TODO

## v1.7.1 — Watch fixes: diff file naming, unified part numbering (see llm_docs/specs/spec-v1.7.1-watch-fixes.md)
- [x] _write_parts: always use numbered filenames (name_1.md, name_2.md), remove single-part special case
- [x] _cmd_diff: include snapshot name in output filename (chat-diff-{snapshot}_N.md)
- [x] _cmd_diff: cross-snapshot naming (chat-diff-{from}-to-{to}_N.md)
- [x] _write_diff_parts: pass snapshot_id for filename template
- [x] _cmd_clean: update glob patterns for new filenames
- [x] Update existing tests expecting chat-code.md to chat-code_1.md

## v1.8.0 — Headers, --query, repo-map mode (see llm_docs/specs/spec-v1.8.0-headers-query-repo-map.md)

## v2.0.0 — Agent API + structural diff (see llm_docs/spec-v2.0.0-agent-api.md)

## Backlog
- [ ] Man page (arachna.1) installed with pip
- [ ] Add more language presets: Go, Rust, Zig, Lua, Elixir, Haskell, Gleam
- [ ] Lazy loading for presets (deferred — low priority)
