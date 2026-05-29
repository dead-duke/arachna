# Changelog

## v0.9.3 — Final fixes

- __main__.py: _cmd_validate использует get_profile() для консистентной валидации
- cache.py, gitignore.py: комментарии к _MAX_HASH_SIZE и _MAX_GITIGNORE_SIZE
- gitignore.py: обработка ValueError от relative_to на всех вызовах
- tests/runner: subprocess.CompletedProcess вместо MagicMock
- __init__.py: bump __version__ to 0.9.3

## v0.9.2 — Pre-release fixes

- hook.py: git_dir.exists() → git_dir.is_dir()
- doctor.py: проверка project_root.is_dir() перед load_gitignore_patterns
- gitignore.py: обработка ValueError от relative_to для симлинков
- __main__.py: _cmd_doctor и _cmd_install_hook без неиспользуемых параметров
- tests/doctor: тесты на _cmd_doctor и _cmd_install_hook с проверкой sys.exit
- __init__.py: bump __version__ to 0.9.2

## v0.9.1 — Version sync

- __init__.py: bump __version__ to 0.9.1
- pyproject.toml: bump version to 0.9.1

## v0.9.0 — Infrastructure

- PyPI-упаковка: authors, keywords, urls в pyproject.toml
- Кроссплатформенные тесты (Windows CI)

## v0.8.5 — Sandbox

- runner.py: dry-run + интерактивное подтверждение для недоверенных команд
- runner.py: _is_safe_command для проверки безопасности в dry-run режиме

## v0.8.4 — Merge

- collector.py: --merge для --profile, добавление вывода к существующему манифесту
- collector.py: _find_next_part_num для нумерации в merge режиме

## v0.8.3 — Git hooks

- hook.py: arachna --install-hook, установка post-commit хука
- hook.py: настраиваемая команда через .arachna.json hook.post-commit
- hook.py: --force для перезаписи существующего хука

## v0.8.2 — Doctor

- doctor.py: arachna --doctor, проверка конфига и корректности контекста
- doctor.py: run_doctor и print_doctor для программного использования

## v0.8.1 — Low fixes

- config.py: DEFAULT_EXCLUDE генерируется из _COMMON_EXCLUDE_DIRS
- splitter.py: токенизаторное усечение через бинарный поиск вместо CHARS_PER_TOKEN
- tests/splitter: тесты на проброс кастомного токенизатора (MagicMock)

## v0.8.0 — God function

- gatherer.py: декомпозиция _collect_named_sections
- gatherer.py: _collect_directory_sections и _collect_file_sections

## v0.7.5 — Truncation API + shlex

- splitter.py: was_truncated через logger.warning вместо print
- runner.py: проверка пустой строки и непарных кавычек перед shlex.split

## v0.7.4 — Sandbox pipe fix

- runner.py: проверка частей пайпа по отдельности в _validate_command
- runner.py: _resolve_base вместо _resolve_command

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
