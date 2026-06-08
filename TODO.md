# TODO

## v2.8.2 — Design/UX + Final polish
- [x] LOW: --mode headers naming — clarify help text
- [x] LOW: Add --no-pre-commands CLI flag
- [x] LOW: _SAFE_TOKENIZERS — configurable via ARACHNA_SAFE_TOKENIZERS env var
- [x] LOW: _EXT_LANG — add .hpp, .cmake, .gradle, .lock, .conf
- [x] LOW: Rate limiting on pre_commands — ARACHNA_PRE_COMMAND_DELAY env var
- [x] LOW: Warn when pre_command produces no output in snapshot
- [x] LOW: _load_builtin_presets cache invalidation based on directory mtime
- [x] LOW: store.py race condition — atomic write for .arachna/.gitignore
- [x] LOW: Cross-snapshot pre_commands diff — show removed lines with - prefix
- [x] LOW: Multi-part diff summary — add part header with change counts
- [ ] Update CHANGELOG for v2.8.2

## Backlog
- [ ] Plugin system for custom formatters and tokenizers
- [ ] Web UI for context browsing
- [ ] IDE integration (VSCode extension)
