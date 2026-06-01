# Changelog

## v1.4.1 — Unified split + audit fixes

- gatherer.py: unified split — single section stream, dense part packing. Removed pre_split_mode/pre_split_marker
- splitter.py: split_sections() for pre-built section lists
- collector.py: _build_toc format-agnostic via named_sections
- __main__.py: extracted _count_file_tokens helper
- runner.py: removed mv, cp from _ALLOWED_COMMANDS
- presets.py: service presets validate detect-paths with explicit preset_name
- .arachna.json: removed pre_split_mode/pre_split_marker from full profile
- tests: test_pre_split_mode.py rewritten for unified split (5 tests)
- tests: test_toc_formats.py — 6 tests for markdown/xml/json TOC
- tests: test_cache_edge.py, test_gitignore_errors.py, test_audit_log_errors.py, test_load_tokenizer_import.py (14 tests)
- tests: removed duplicate external+preset_name tests from test_presets.py
- 436 tests, 93% coverage

## v1.4.0 — Security hardening + cleanup

- tokenizer.py: removed fallback to sys.modules in _is_safe_tokenizer, deny by default
- runner.py: removed chmod, chown from _ALLOWED_COMMANDS
- gatherer.py: skip symlinks in _scan_directories with warning
- gatherer.py: decomposed _assemble_content into _assemble_command_content and _assemble_file_content
- __main__.py: --version via argparse action='version'
- tests/runner: audit log coverage (3 tests)
- tests/tokenizer: test_local_file_check.py (6 tests)
- tests/runner: test_runner_edge.py (7 tests)
- tests/formatter: test_should_skip_binary.py (9 tests)
- 414 tests, 93% coverage

## v1.3.0 — Multi-source split modes + bug fixes

- gatherer.py: pre_split_mode and pre_split_marker — separate splitting of pre_commands and files
- runner.py: _split_pipe_parts respects shell quoting, word-boundary matching for _BLOCKED_PATTERNS (BUG-001)
- presets.py: c_cpp detect reduced to CMakeLists.txt only (BUG-004)

## v1.2.2 — CLI consistency

- init.py: run_interactive filters autodetection by --preset
- tests/presets: tests for external presets with preset_name
- tests/init: test_init_preset_param.py — 5 tests for --preset in interactive mode

## v1.2.1 — Security fix

- tokenizer.py: _is_safe_tokenizer with whitelist and stdlib blocking
- tokenizer.py: load_tokenizer raises ValueError for unsafe modules
- presets.py: tokenizer validation in load_presets_from_file
- presets.py: detect_presets with preset_name validates detect-paths
- presets.py: _VALID_PRESET_KEYS includes "tokenizer"
- tests/tokenizer: test_unsafe_rejection.py — 12 tests
- tests/presets: tests for unsafe tokenizer in load_presets_from_file
- tests/presets: tests for explicit preset_name with matching/non-matching paths

## v1.2.0 — Presets as config

- presets.py: load_presets_from_file for external presets.json
- presets.py: validation of user presets
- __main__.py: --preset for preset selection during init
- init.py: run_defaults and run_interactive accept preset
- tests/presets: 42 tests for detect, load, merge, external presets

## v1.1.0 — Language & engine presets

- presets.py: 16 presets (Python, JS, Godot, Unity, C/C++, C#, Swift, Kotlin/Java, Ruby, PHP, Docker, Terraform, docs, tests, config, git)
- init.py: rewritten on presets.py, autodetection of all project types
- formatter.py: extensions gd, cs, swift, kt, java, rb, php, tf, dockerfile
- tests/init: tests for all new presets

## v1.0.2 — Fix --version CLI

- __main__.py: handle --version before argparse to avoid mutually_exclusive_group conflict
- __init__.py: bump __version__ to 1.0.2

## v1.0.1 — Windows test fixes

- tests/cache: _make_entry uses real SHA256 hash instead of "dummy"
- tests/cache: time.sleep(0.01) in test_get_changed_files_modified and test_get_changed_files_mixed
- tests/formatter: test_permission_denied skipped on Windows (chmod 0o000 unsupported)
- tests/gatherer: time.sleep(0.01) in test_collect_sections_incremental_detects_modified
- tests/hook: S_IXUSR check only on Unix (Windows does not support executable bits)
- __init__.py: bump __version__ to 1.0.1
- pyproject.toml: bump version to 1.0.1

## v1.0.0 — Public release

- First public release on PyPI
- __init__.py: bump __version__ to 1.0.0
- pyproject.toml: bump version to 1.0.0

## v0.9.5 — GitHub prep

- pyproject.toml: URLs updated to github.com/dead-duke/arachna
- README.md: added repo link, badges, safety section, doctor, hooks, full commands and options
- __init__.py: bump __version__ to 0.9.5

## v0.9.4 — Final polish

- runner.py: import json moved to module level
- gatherer.py: _assemble_content — shared content assembly for collect and dry_run
- collector.py: collect uses _assemble_content, removed duplicated assembly logic
- __init__.py: bump __version__ to 0.9.4
- pyproject.toml: bump version to 0.9.4

## v0.9.3 — Final fixes

- __main__.py: _cmd_validate uses get_profile() for consistent validation
- cache.py, gitignore.py: comments for _MAX_HASH_SIZE and _MAX_GITIGNORE_SIZE
- gitignore.py: ValueError handling from relative_to on all calls
- tests/runner: subprocess.CompletedProcess instead of MagicMock
- __init__.py: bump __version__ to 0.9.3

## v0.9.2 — Pre-release fixes

- hook.py: git_dir.exists() → git_dir.is_dir()
- doctor.py: check project_root.is_dir() before load_gitignore_patterns
- gitignore.py: ValueError handling from relative_to for symlinks
- __main__.py: _cmd_doctor and _cmd_install_hook without unused parameters
- tests/doctor: tests for _cmd_doctor and _cmd_install_hook with sys.exit check
- __init__.py: bump __version__ to 0.9.2

## v0.9.1 — Version sync

- __init__.py: bump __version__ to 0.9.1
- pyproject.toml: bump version to 0.9.1

## v0.9.0 — Infrastructure

- PyPI packaging: authors, keywords, urls in pyproject.toml
- Cross-platform tests (Windows CI)

## v0.8.5 — Sandbox

- runner.py: dry-run + interactive confirmation for untrusted commands
- runner.py: _is_safe_command for safety check in dry-run mode

## v0.8.4 — Merge

- collector.py: --merge for --profile, append output to existing manifest
- collector.py: _find_next_part_num for numbering in merge mode

## v0.8.3 — Git hooks

- hook.py: arachna --install-hook, post-commit hook installation
- hook.py: configurable command via .arachna.json hook.post-commit
- hook.py: --force to overwrite existing hook

## v0.8.2 — Doctor

- doctor.py: arachna --doctor, config validation and context integrity check
- doctor.py: run_doctor and print_doctor for programmatic use

## v0.8.1 — Low fixes

- config.py: DEFAULT_EXCLUDE generated from _COMMON_EXCLUDE_DIRS
- splitter.py: tokenizer-based truncation via binary search instead of CHARS_PER_TOKEN
- tests/splitter: tests for custom tokenizer passthrough (MagicMock)

## v0.8.0 — God function

- gatherer.py: decomposed _collect_named_sections
- gatherer.py: _collect_directory_sections and _collect_file_sections

## v0.7.5 — Truncation API + shlex

- splitter.py: was_truncated via logger.warning instead of print
- runner.py: empty string and unclosed quotes check before shlex.split

## v0.7.4 — Sandbox pipe fix

- runner.py: validate each pipe part individually in _validate_command
- runner.py: _resolve_base instead of _resolve_command

## v0.7.3 — Test stability

- tests: replace os.chdir with tmp_path/monkeypatch (all modules)
- tests/runner: mock subprocess.run
- tests/config: isolate from parent .arachna.json
- tests/gatherer/test_incremental.py: rewritten as integration test

## v0.7.2 — Architecture cleanup

- gatherer.py: removed global _TOKENIZE, get_tokenizer, set_tokenizer
- collector.py: removed fallback write_text in save_manifest
- splitter.py: extracted CHARS_PER_TOKEN, added truncated flag to _handle_single
- config.py + gitignore.py: unified EXCLUDED_DIRS
- CHANGELOG.md: fixed disinformation and duplication

## v0.7.1 — Critical fixes

- runner.py: removed interpreters (python, node, ruby, perl, php) from _ALLOWED_COMMANDS
- splitter.py: fixed tokenizer passthrough in _build_parts (keyword args)
- __main__.py: _apply_args_to_profile returns copy, does not mutate original

## v0.7.0 — Security sandbox, architecture cleanup

- runner.py: sandbox validation _validate_command with _BLOCKED_PATTERNS and _ALLOWED_COMMANDS
- runner.py: audit log of commands in .arachna_commands.log
- cache.py: atomic write via tempfile + os.replace
- gitignore.py: size limit, EXCLUDED_DIRS filtering, binary file detection
- formatter.py: size check before read_text, verbose skip reasons
- __main__.py: refactored _cmd_all and _cmd_single via _run_profile
- gatherer.py: set_tokenizer/get_tokenizer deprecated
- 179 tests, 90% coverage

## v0.6.0 — Pluggable tokenizer

- tokenizer.py: load_tokenizer(spec)
- tokenizer field in profile
- Plumbed through collector → gatherer
- 179 tests, 90% coverage

## v0.5.0 — Tests, safety, audit fixes

- Tests: cache, completion, init, formatter xml/json, incremental, manifest
- Removed compress_indent (unsafe for Python)
- Safe compression: blank lines + trailing spaces
- Shell security warning in README
- LICENSE (MIT)
- 175 tests, 90% coverage

## v0.4.2 — Audit fixes

- Removed dead code in gatherer.py
- Fixed CJK token tests
- README: token margin recommendation

## v0.4.1 — Table of contents + manifest

- TOC in each part: file list
- chat-manifest.md: summary of all collected files

## v0.4.0 — Shell completion + hooks

- bash and zsh completion (arachna --completion bash|zsh)
- post_commands in profile: run after collection
- 144 tests, 70% coverage

## v0.3.0 — Compress, incremental, formats, binary

- Whitespace compression (--compress)
- Incremental mode: mtime cache (--incremental)
- section_format: markdown (default), xml, json (--format)
- include_binary: base64 with size/extension filters
- 140 tests

## v0.2.2 — Git split marker, per-profile manifest cleanup

- git split_marker: \n=== COMMIT:
- --all: clean all files, rebuild all profiles
- --profile: clean only this profile

## v0.2.1 — arachna init

- --init interactive + --defaults auto-detect

## v0.2.0 — Single file output, manifest, test reorg

- chat-code.md, manifest, arachna_context/, 129 tests, 90% coverage

## v0.1.5 — Shebang Detection
## v0.1.4 — Tests & Bugfixes
## v0.1.3 — Validate & Gitignore
## v0.1.2 — Dry-run, renderer, pre-commit
## v0.1.1 — Tests + fixes
## v0.1.0 — MVP
