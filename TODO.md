# TODO

## v2.9.0 — Security hardening (details: llm_docs/specs/spec-v2.9.0-security.md)
- [ ] HIGH SEC-01: File read via allowed commands — add allow_file_args param to run_command, restrict internal calls
- [ ] HIGH SEC-02: File write via shell redirection — reject > and < in shell commands
- [ ] HIGH SEC-03: Path traversal via snapshot names — validate re.match(r'^[\w][\w.-]*$', snapshot_id)
- [ ] HIGH SEC-04: Dynamic import side effects — validate top-level statements in tokenizer files
- [ ] MEDIUM ARCH-02: TOC content matching — split_sections returns section_indices, _write_parts uses direct indexing
- [ ] MEDIUM SEC-05: Local file inclusion in --presets-update — validate url.startswith(('http://', 'https://'))
- [ ] LOW CQ-01: gatherer.py double header generation — pass pre-generated header to _apply_repo_map_to_section
- [ ] LOW CQ-03: gatherer.py pattern traversal — reject patterns containing ".."
- [ ] LOW CQ-05: store.py write_object race condition — atomic write via tempfile + os.replace
- [ ] Update CHANGELOG for v2.9.0

## v2.9.1 — Architecture + Code Quality fixes (details: llm_docs/specs/spec-v2.9.1-architecture.md)
- [ ] MEDIUM ARCH-01: differ_structural.py brace matching — strip strings/comments before _extract_braced_block
- [ ] LOW CQ-02: gatherer.py _collect_import_graph re-parses — extract deps/exports from section content
- [ ] LOW CQ-04: watcher.py similarity without max_size — limit files to 1MB
- [ ] LOW CQ-06: splitter.py split_sections no truncation — add truncation like _handle_single
- [ ] LOW CQ-07: differ.py _format_added hardcoded 4 chars/token — pass tokenizer param
- [ ] LOW CQ-08: cache.py get_changed_files mutates input — return updated_cache instead
- [ ] LOW CQ-09: differ_structural.py _parse_python_blocks returns {} on SyntaxError — return None, fallback to text diff
- [ ] LOW CQ-10: store.py create_snapshot not atomic — document tradeoff in docstring
- [ ] LOW CQ-11: gitignore.py incomplete implementation — document limitations in docstring
- [ ] LOW CQ-12: collector.py threading.Lock fallback — add os.open(O_CREAT | O_EXCL) alternative
- [ ] LOW CQ-13: splitter.py binary search non-monotonic guard — add max iterations limit
- [ ] LOW CQ-14: init.py EOFError in non-interactive mode — catch EOFError, return default
- [ ] LOW CQ-15: presets.py fetch_presets hardcoded timeout — add ARACHNA_PRESETS_TIMEOUT env var
- [ ] LOW TEST-01: runner.py shell=True not verified in tests — add assert_called_with(shell=True)
- [ ] LOW TEST-02: watcher.py _diff_file_sets isolated unit tests
- [ ] LOW TEST-03: gatherer.py _collect_import_graph edge case tests
- [ ] LOW TEST-04: splitter.py binary search custom tokenizer tests
- [ ] Update CHANGELOG for v2.9.1

## v2.9.2 — Final polish
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
