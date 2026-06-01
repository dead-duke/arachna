# TODO

## v1.4.2 — Audit LOW fixes + compression stats bug
- [x] gatherer.py: fix compression stats — raw_tokens from named_sections, not sections
- [x] runner.py: remove touch from _ALLOWED_COMMANDS
- [x] __main__.py: extract _print_collected helper from _cmd_all/_cmd_single
- [x] hook.py: remove S_IXOTH from chmod, keep S_IXUSR | S_IXGRP
- [x] __main__.py: pass tokens from memory to _write_manifest instead of disk read
- [x] tests/presets: remove duplicate external+preset_name tests from test_presets.py
- [x] tests/collector: add test_toc_with_compress to test_toc_formats.py
- [x] __main__.py: use copy.deepcopy in _apply_args_to_profile
- [x] tokenizer.py: document check order in _is_safe_tokenizer docstring

## Backlog
- [ ] Unreal Engine preset
- [ ] IDE integration (VS Code extension)
- [ ] Web UI for visual profile editor
