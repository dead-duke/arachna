# TODO

## v2.8.2 — Design/UX + Final polish
- [ ] LOW: --mode headers naming — clarify README or rename
- [ ] LOW: Add --no-pre-commands / --skip-pre-commands CLI flag
- [ ] LOW: _SAFE_TOKENIZERS — configurable via ARACHNA_SAFE_TOKENIZERS env var
- [ ] LOW: _EXT_LANG — add .hpp, .cmake, .gradle, .lock, .conf
- [ ] LOW: Rate limiting on pre_commands — configurable delay between executions
- [ ] LOW: Warn when pre_command produces no output in snapshot
- [ ] LOW: _load_builtin_presets cache invalidation based on directory mtime
- [ ] LOW: store.py race condition — atomic write for .arachna/.gitignore
- [ ] LOW: Cross-snapshot pre_commands diff — show removed lines with - prefix
- [ ] LOW: Multi-part diff summary — add part header with change counts
- [ ] Update CHANGELOG for v2.8.2

## Backlog
- [ ] Plugin system for custom formatters and tokenizers
- [ ] Web UI for context browsing
- [ ] IDE integration (VSCode extension)
