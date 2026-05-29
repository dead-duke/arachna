# Changelog

## v0.7.4 — Sandbox pipe fix

- runner.py: проверка частей пайпа по отдельности в _validate_command

## v0.7.3 — Test stability

- tests: замена os.chdir на tmp_path/monkeypatch (все модули)
- tests/runner: замокать subprocess.run
- tests/config: изоляция от родительского .arachna.json
- tests/gatherer/test_incremental.py: переписан на интеграционный тест

## v0.7.2 — Architecture cleanup

- gatherer.py: удалено глобальное _TOKENIZE, get_tokenizer, set_tokenizer
- collector.py: убран fallback write_text в save_manifest
- splitter.py: вынесен CHARS_PER_TOKEN, добавлен флаг truncated в _handle_single
- config.py + gitignore.py: унифицированы EXCLUDED_DIRS
- CHANGELOG.md: исправлена дезинформация и дублирование

## v0.7.1 — Critical fixes

- runner.py: удалены интерпретаторы (python, node, ruby, perl, php) из _ALLOWED_COMMANDS
- splitter.py: исправлен проброс tokenizer в _build_parts (keyword args)
- __main__.py: _apply_args_to_profile возвращает копию, не мутирует оригинал

## v0.7.0 — Security sandbox, architecture cleanup

- runner.py: sandbox-валидация _validate_command с _BLOCKED_PATTERNS и _ALLOWED_COMMANDS
- runner.py: аудит-лог команд в .arachna_commands.log
- cache.py: атомарная запись через tempfile + os.replace
- gitignore.py: ограничение размера, фильтрация EXCLUDED_DIRS, детект бинарных файлов
- formatter.py: проверка размера до read_text, verbose skip reasons
- __main__.py: рефакторинг _cmd_all и _cmd_single через _run_profile
- gatherer.py: set_tokenizer/get_tokenizer deprecated
- 179 tests, 90% coverage

## v0.6.0 — Pluggable tokenizer

- tokenizer.py: load_tokenizer(spec)
- tokenizer field в profile
- Проброшен через collector → gatherer
- 179 tests, 90% coverage

## v0.5.0 — Tests, safety, audit fixes

- Тесты: cache, completion, init, formatter xml/json, incremental, manifest
- Убран compress_indent (небезопасный для Python)
- Безопасное сжатие: пустые строки + trailing spaces
- Shell security warning в README
- LICENSE (MIT)
- 175 tests, 90% coverage

## v0.4.2 — Audit fixes

- Убран мёртвый код в gatherer.py
- Исправлены CJK token тесты
- README: рекомендация по token margin

## v0.4.1 — Table of contents + manifest

- TOC в каждой части: список файлов
- chat-manifest.md: сводка всех собранных файлов

## v0.4.0 — Shell completion + hooks

- bash и zsh completion (arachna --completion bash|zsh)
- post_commands в профиле: запуск после коллекта
- 144 tests, 70% coverage

## v0.3.0 — Compress, incremental, formats, binary

- Whitespace compression (--compress)
- Инкрементальный режим: mtime кэш (--incremental)
- section_format: markdown (default), xml, json (--format)
- include_binary: base64 с фильтрами по размеру и расширению
- 140 tests

## v0.2.2 — Git split marker, per-profile manifest cleanup

- git split_marker: \n=== COMMIT:
- --all: очистка всех файлов, пересборка всех профилей
- --profile: очистка только этого профиля

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
