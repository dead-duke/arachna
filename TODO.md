# TODO

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
