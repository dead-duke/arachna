# TODO

## v2.9.1 — Architecture + Code Quality fixes
- [x] MEDIUM ARCH-01: differ_structural.py brace matching — strip strings/comments before _extract_braced_block
- [x] LOW CQ-02: gatherer.py _collect_import_graph re-parses — extract deps/exports from section content with fallback
- [x] LOW CQ-04: watcher.py similarity without max_size — limit files to 1MB
- [x] LOW CQ-06: splitter.py split_sections no truncation — add truncation like _handle_single
- [x] LOW CQ-07: differ.py _format_added hardcoded 4 chars/token — pass tokenizer param with binary search
- [x] LOW CQ-08: cache.py get_changed_files mutates input — document mutation in docstring
- [x] LOW CQ-09: differ_structural.py _parse_python_blocks returns {} on SyntaxError — return None, fallback to text diff
- [x] LOW CQ-10: store.py create_snapshot not atomic — document tradeoff in docstring
- [x] LOW CQ-11: gitignore.py incomplete implementation — document limitations in docstring
- [x] LOW CQ-12: collector.py threading.Lock fallback — add os.open(O_CREAT | O_EXCL) alternative
- [x] LOW CQ-13: splitter.py binary search non-monotonic guard — add max iterations limit
- [x] LOW CQ-14: init.py EOFError in non-interactive mode — catch EOFError, return default
- [x] LOW CQ-15: presets.py fetch_presets hardcoded timeout — add ARACHNA_PRESETS_TIMEOUT env var
- [ ] Update CHANGELOG for v2.9.1

## v2.9.2 — Final polish
- [ ] LOW TEST-01: runner.py shell=True not verified in tests — add assert_called_with(shell=True)
- [ ] LOW TEST-02: watcher.py _diff_file_sets isolated unit tests
- [ ] LOW TEST-03: gatherer.py _collect_import_graph edge case tests
- [ ] LOW TEST-04: splitter.py binary search custom tokenizer tests
- [ ] LOW TEST-05: presets.py fetch_presets timeout test
- [ ] LOW: gatherer.py include_header naming — document behavior clearly
- [ ] LOW: watcher.py isolated tests — add unit tests for helper functions
- [ ] LOW: presets.py timeout not tested — add slow network mock test
- [ ] LOW: gatherer.py _collect_import_graph caching — cache per file list
- [ ] LOW: formatter.py _is_binary_allowed — add direct unit tests
- [ ] LOW: cache.py SHA256 fallback path — add explicit test for mtime within tolerance + size differs
- [ ] Update CHANGELOG for v2.9.2

## Backlog
- [ ] Plugin system for custom formatters and tokenizers
- [ ] Web UI for context browsing
- [ ] IDE integration (VSCode extension)
