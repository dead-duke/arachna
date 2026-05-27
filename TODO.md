# TODO

## v0.1.0 — MVP
- [x] tokenizer, config, collector, gatherer, splitter, formatter, runner, CLI

## v0.1.1 — Tests + fixes
- [x] 29 tests

## v0.1.2 — Dry-run & Developer Experience
- [x] dry_run, renderer, Makefile, pre-commit

## v0.1.3 — Validate & Gitignore
- [x] validator, gitignore, default profile

## v0.1.4 — Tests & Bugfixes
- [x] 102 tests, 65% coverage

## v0.1.5 — Shebang Detection
- [x] shebang detection, 107 tests

## v0.2.0 — Single file output, manifest, test reorg
- [x] chat-code.md, manifest, arachna_context/, 129 tests, 90% coverage

## v0.2.1 — arachna init
- [x] --init interactive + --defaults auto-detect

## v0.2.2 — Git split marker, per-profile manifest cleanup
- [x] \n=== COMMIT: marker, --profile keeps other profiles

## v0.3.0 — Compress, incremental, formats, binary
- [x] compress, incremental, section_format, include_binary, 140 tests

## v0.4.0 — Shell completion + hooks
- [x] bash/zsh completion, post_commands, 144 tests

## v0.4.1 — Table of contents + manifest
- [x] TOC in each part, chat-manifest.md

## v0.4.2 — Audit fixes
- [x] Removed dead code, fixed CJK tests, README token margin

## v0.5.0 — Tests, safety, audit, tokenizer prep
- [x] Removed compress_indent (unsafe), safe compression only
- [x] Shell security warning, LICENSE, pyproject.toml classifiers
- [x] formatter: verbose skip reasons
- [x] splitter: separator for xml/json
- [x] Tests: cache, completion, init, formatter, incremental, manifest
- [x] 175 tests, 90% coverage

## v0.6.0 — Pluggable tokenizer
- [x] load_tokenizer(spec) в tokenizer.py
- [x] tokenizer field в profile
- [x] Plumbed через collector → gatherer
- [x] 179 tests, 90% coverage

## v0.7.0 — Security sandbox, architecture cleanup
- [x] runner.py: убрать интерпретаторы из _ALLOWED_COMMANDS
- [x] runner.py: sandbox-валидация + аудит-лог
- [x] gatherer.py: set_tokenizer/get_tokenizer deprecated, _TOKENIZE сохранён для совместимости
- [x] __main__.py: рефакторинг _cmd_all/_cmd_single через _run_profile
- [x] cache.py: атомарная запись через tempfile + os.replace
- [x] gitignore.py: ограничение размера + EXCLUDED_DIRS
- [x] formatter.py: проверка размера до read_text
- [x] 179 tests, 90% coverage

## v0.7.1 — Pluggable tokenizer bugfixes
- [ ] splitter: пробросить tokenizer в _build_parts и _handle_single
- [ ] gatherer: dry_run передаёт tokenizer в split
- [ ] __main__: _run_profile не мутирует profile (копия перед _apply_args_to_profile)

## v0.7.2 — Архитектурные фиксы
- [ ] collector: атомарная запись манифеста (убрать fallback write_text)
- [ ] splitter: вынести CHARS_PER_TOKEN, добавить флаг truncated в _handle_single
- [ ] config: унифицировать EXCLUDED_DIRS с gitignore.py
- [ ] renderer: вынести магические значения в константы MIN_PCT_*

## v0.7.3 — Тестопригодность
- [ ] tests: замена os.chdir на tmp_path/monkeypatch
- [ ] tests/runner: замокать subprocess.run
- [ ] tests/config: изоляция от родительского .arachna.json

## v1.0.0 — Public release
- [ ] pip install arachna (publish to PyPI)
- [ ] Sandbox для command (контейнер/nsjail или dry-run + подтверждение)
- [ ] Кроссплатформенные тесты (Windows CI)
- [ ] arachna install-hook (git post-commit)
- [ ] Coverage ≥ 95%

## Backlog
- [ ] CI/CD (GitHub Actions)
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
