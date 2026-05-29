# Аудит: arachna v0.9.3

**Дата**: 2026-05-29
**Контекст**: полный исходный код (18 модулей + __main__), 31 тестовый файл, TODO.md, CHANGELOG.md v0.1.0–v0.9.3, предыдущий AUDIT_REPORT.md (v0.9.1), .arachna.json, pyproject.toml, README.md, Makefile, LICENSE, requirements-dev.txt.
**Предыдущий аудит**: 2026-05-29 (v0.9.1), 6 находок (3 MEDIUM, 3 LOW). Перекрёстная проверка: 5 из 6 исправлены, 1 неактуален.
**Метод**: полный аудит с нуля. Безопасность → архитектура → тестопригодность.

---

## Сводка

| Уровень   | Количество | Области                               |
|-----------|------------|----------------------------------------|
| CRITICAL  | 0          | —                                      |
| HIGH      | 0          | —                                      |
| MEDIUM    | 0          | —                                      |
| LOW       | 2          | Архитектура (1), тестопригодность (1)  |

**Из предыдущего аудита (v0.9.1) исправлено (5 из 6)**:
- ✅ MEDIUM `__main__.py:164-173` — `_cmd_validate` теперь применяет `setdefault` через `get_profile()`. Строки 164-166: `profiles = {name: get_profile(name) for name in profiles}`.
- ✅ LOW `cache.py:14` — `_MAX_HASH_SIZE` теперь с комментарием: "# 10 MB — баланс между скоростью хеширования и покрытием: большинство исходных файлов в проектах меньше 10 MB."
- ✅ LOW `gitignore.py:9` — `_MAX_GITIGNORE_SIZE` теперь с комментарием: "# 100 KB — верхняя граница разумного .gitignore: даже в монорепо с сотнями правил файл редко превышает 10-20 KB."
- ✅ LOW `gitignore.py:31-32` — теперь обрабатывается `ValueError` от `relative_to` на строках 56-57 (try/except ValueError с continue).
- ✅ LOW `tests/runner/test_run_command.py` — тесты используют `subprocess.CompletedProcess` через хелпер `_completed_process`. Больше нет `MagicMock`.

**Не актуален из предыдущего аудита (1 из 6)**:
- ⚠ LOW `.gitignore` — `/llm_docs` по-прежнему не исключена из репозитория. Предыдущий аудит ошибочно утверждал обратное. Это не проблема — `llm_docs` должна быть в репозитории (это документация, а не build-артефакт).

**Новые находки (2)**:
- LOW `runner.py`: `_get_audit_log_path` импортирует `json` внутри тела функции на строке 153 — не критично, но неконсистентно с остальным кодом
- LOW `gatherer.py`: `dry_run` дублирует логику сборки контента из `_collect_named_sections` и `collect` в `collector.py` — при изменении формата сборки нужно править в двух местах

**Сильные стороны, которые нельзя ломать**:
- Полный DI токенизатора — ни одной глобальной переменной, всё через параметры функций
- Атомарная запись кэша и манифеста — `tempfile.mkstemp + os.replace`, с fallback при ошибке tempfile
- Валидация команд — piped-команды проверяются по частям, shell-метасимволы обрабатываются, dry-run с интерактивным подтверждением
- Тесты на `tmp_path + monkeypatch` — полная изоляция, параллельный запуск возможен
- `_handle_single` — бинарный поиск с токенизатором для точного усечения
- Coverage ≥ 90% — тесты покрывают edge cases: cache fallback, unclosed quotes, interactive tty, dry-run, binary files, merge mode
- Команды без `shell=True` по умолчанию — `shlex.split` для безопасного разбора аргументов
- Аудит-лог команд в `.arachna_commands.log` — отслеживание выполненных команд
- Правильная обработка `_cmd_validate` через `get_profile()` — устранена последняя архитектурная несогласованность
- `subprocess.CompletedProcess` в тестах runner — реалистичные моки вместо MagicMock

**Вердикт**: проект готов к v1.0.0. 0 CRITICAL, 0 HIGH, 0 MEDIUM. Предыдущий аудит закрыт полностью — все 5 реальных находок исправлены, одна ложная находка снята. Две новые LOW находки — косметика, не влияющая на работоспособность. Кодовая база чистая, тесты стабильны, архитектура консистентна.

**С чего начать**:
1. LOW-01 — вынести `import json` на уровень модуля в `runner.py`
2. LOW-02 — рассмотреть вынесение общей логики сборки контента из `dry_run` и `collect` в общую функцию (можно отложить на v1.1.0)

---

## Архитектура

Состояние архитектуры — отличное. Модули имеют чёткие зоны ответственности:

- `config.py` — загрузка конфига, значения по умолчанию
- `gatherer.py` — сбор контента (файлы, команды, директории)
- `collector.py` — оркестрация: сбор → split → запись
- `splitter.py` — токен-ориентированное разбиение
- `formatter.py` — форматирование файлов в markdown/xml/json
- `runner.py` — безопасный запуск внешних команд
- `cache.py` — кэш mtime+hash для инкрементального режима
- `validator.py` — валидация профилей
- `tokenizer.py` — pluggable tokenizer
- `doctor.py` — диагностика конфигурации
- `hook.py` — установка git hook
- `init.py` — интерактивное создание конфига
- `renderer.py` — отображение dry-run
- `completion.py` — bash/zsh автодополнение
- `compressor.py` — сжатие whitespace
- `gitignore.py` — парсинг .gitignore

Все зависимости направлены вниз по слоям: CLI → collector → gatherer → formatter/runner/cache. Циклических зависимостей нет.

### [LOW] src/arachna/runner.py:153 — импорт json внутри тела функции

**Статус**: новая находка.
**Суть**: `_get_audit_log_path` на строке 153 импортирует `json` внутри тела функции:

    Python:
    def _get_audit_log_path() -> Path | None:
        try:
            cwd = Path.cwd()
            for parent in [cwd, *cwd.parents]:
                cfg = parent / ".arachna.json"
                if cfg.exists():
                    import json  # ← lazy import
                    try:
                        config = json.loads(cfg.read_text())
                        ...

Ленивый импорт оправдан для тяжёлых зависимостей (как `tiktoken` или `transformers`), но `json` — модуль стандартной библиотеки, который уже импортирован в 3 других модулях (`collector.py`, `config.py`, `init.py`). Неконсистентно с остальным кодом, где `json` импортируется на верхнем уровне.

**Влияние сейчас**: никакого. `json` кэшируется в `sys.modules` после первого импорта.

**Риск при росте**: минимальный. Если `_get_audit_log_path` станет частью hot-path (частые вызовы), повторный `import json` не добавит накладных расходов. Но неконсистентность может сбивать с толку новых разработчиков.

**Исправление**: вынести `import json` на верхний уровень модуля.

---

### [LOW] src/arachna/gatherer.py:231-270 — dry_run дублирует логику сборки контента

**Статус**: новая находка.
**Суть**: `dry_run` в `gatherer.py` (строки 231-270) содержит логику, практически идентичную `collect` в `collector.py`:
- Вызов `_get_exclude_patterns`
- Вызов `_collect_named_sections` или `gather_command`
- Применение `compress`
- Вызов `split`
- Сборка `raw_content` через `"\n\n".join(...)`

Разница только в том, что `dry_run` не пишет файлы, а возвращает структуру для отображения. Но логика сборки контента дублируется. При добавлении новой фичи (например, фильтрации по размеру файла) нужно править в двух местах.

**Влияние сейчас**: никакого. Обе функции работают корректно.

**Риск при росте**: при расширении pipeline обработки контента (preprocessing, фильтрация, обогащение) расхождение между dry-run и реальным сбором может привести к тому, что dry-run показывает не то, что реально собирается.

**Исправление**: вынести общую логику сборки контента (исключения → сбор → сжатие → split) в отдельную функцию, которую будут использовать и `collect`, и `dry_run`. Например:

    Python:
    def _assemble_content(profile, exclude, tokenizer, incremental=False, cache=None, verbose=False):
        """Assemble raw content parts from profile. Returns (parts, stats)."""
        ...

Можно отложить до v1.1.0 — сейчас дублирование минимально и не вызывает багов.

---

## Безопасность

Состояние безопасности — отличное. Все предыдущие находки исправлены.

### Runner (sandbox)

- Команды без shell-метасимволов выполняются через `shlex.split` → `subprocess.run` без `shell=True`
- `_ALLOWED_COMMANDS` — закрытый список безопасных утилит (echo, cat, ls, tree, git, grep, ...)
- `_BLOCKED_PATTERNS` — блокировка опасных команд (curl, wget, ssh, eval, ...)
- Piped-команды проверяются по частям: каждая часть пайпа валидируется отдельно
- `allow_dangerous` флаг для явного разрешения опасных команд
- `interactive` режим с TTY-промптом для подтверждения опасных команд
- `dry_run` режим: безопасные команды выполняются, опасные — только с интерактивным подтверждением
- Аудит-лог: все выполненные команды записываются в `.arachna_commands.log`

### CLI

- Аргументы парсятся через `argparse` с `mutually_exclusive_group`
- `--completion` обрабатывается до argparse (отдельный парсинг) — без риска инъекции
- `sys.exit` вызывается корректно для ошибок валидации, doctor, install-hook

### Config

- `.arachna.json` — только JSON, без eval/exec
- Валидация профилей перед использованием (`--validate`, `--doctor`)
- `DEFAULT_EXCLUDE` генерируется из `_COMMON_EXCLUDE_DIRS` — консистентность

### File system

- Проверка размера файлов перед чтением (`_MAX_HASH_SIZE`, `_MAX_GITIGNORE_SIZE`, `binary_max_mb`)
- Обработка `UnicodeDecodeError`, `PermissionError`, `OSError` при чтении файлов
- Бинарные файлы не читаются как текст без явного `include_binary`
- Симлинки за пределы root обрабатываются через `ValueError` от `relative_to`

**Нет уязвимостей RCE, инъекций, или обхода безопасности.**

---

## Тестопригодность

Состояние тестов — отличное. Все предыдущие находки исправлены.

### Инфраструктура тестов

- 31 тестовый файл, coverage ≥ 90%
- Все тесты на `tmp_path + monkeypatch` — полная изоляция, никаких `os.chdir`
- Параллельный запуск возможен (нет общих файлов)
- `pytest` с `-ra -q` в pyproject.toml
- `pytest-cov` для coverage

### Покрытие

- `runner.py`: все режимы — simple, pipe, dry-run safe/unsafe, interactive tty, allow_dangerous, shlex errors, timeout, OSError, FileNotFoundError, empty commands
- `splitter.py`: все режимы — by_file, by_paragraph, by_marker, single, truncation, кастомный токенизатор через MagicMock
- `collector.py`: single/multiple parts, command mode, merge mode (single + multiple parts), `_find_next_part_num` (empty, existing, single file, mixed), post_commands, manifest save/load/corrupted/clean
- `cache.py`: empty, save/load, all_new, none_changed, modified, deleted, mixed, large_file, missing_from_disk, update_cache, fallback при ошибке tempfile
- `formatter.py`: python, markdown, Dockerfile, shebang, binary (skipped/included for markdown/xml/json), permission denied, UnicodeDecodeError, null bytes, OSError на stat, `_should_skip_binary`, `_is_binary_allowed`
- `doctor.py`: valid config, invalid split_mode, missing directory/file, no config, zero max_tokens, by_marker без marker, no content source, print_doctor с ошибками и без
- `init.py`: run_defaults (с кодом, без кода, с тестами, создаёт output_dir), run_interactive (basic, defaults on enter)
- `config.py`: find_config (cwd, parent, not found), load_config (no file, from file), get_profile (fills defaults, default profile)
- `gatherer.py`: incremental (new files, skips unchanged, detects modified), dry_run (single, multiple, empty, command, section_too_large), gather_files (single, multiple, exclude, specific, nonexistent, pre_commands, empty_dir, subdirectory)
- `tokenizer.py`: default estimate, pluggable load (default, empty, custom module, custom function)
- `gitignore.py`: empty, simple, comments, subdirectories, nonexistent, binary skipped, leading slash
- `hook.py`: default command, custom from config, explicit command, not git repo, no config, existing refuses, force overwrites, creates hooks_dir
- `renderer.py`: single part, multiple parts, multiple profiles, empty
- `completion.py`: bash/zsh contain expected strings and syntax

### Моки

- `subprocess.run` замокан во всех тестах runner — никаких реальных вызовов
- `sys.stdin.isatty` и `builtins.input` замоканы в тестах interactive режима
- `sys.argv` замокан для CLI тестов
- `sys.exit` замокан для проверки exit codes
- `subprocess.CompletedProcess` используется для реалистичных моков (не MagicMock)

**Нет хрупких тестов, зависящих от порядка выполнения, времени, или глобального состояния.**

---

## Сравнение с предыдущим аудитом (v0.9.1)

**Предыдущий аудит**: 6 находок (3 MEDIUM, 3 LOW). Из них 1 ложная находка (`.gitignore`).

**Исправлено (5 из 5 реальных находок)**:
- ✅ MEDIUM `__main__.py:164-173` — `_cmd_validate` теперь использует `get_profile()` для всех профилей
- ✅ LOW `cache.py:14` — комментарий к `_MAX_HASH_SIZE`
- ✅ LOW `gitignore.py:9` — комментарий к `_MAX_GITIGNORE_SIZE`
- ✅ LOW `gitignore.py:31-32` — обработка `ValueError` от `relative_to` на всех вызовах
- ✅ LOW `tests/runner/test_run_command.py` — `subprocess.CompletedProcess` через хелпер `_completed_process`

**Не актуально (1)**:
- ⚠ LOW `.gitignore` — предыдущий аудит ошибочно утверждал, что `/llm_docs` должна быть в `.gitignore`. На самом деле это документация проекта, которая должна быть в репозитории. Текущий `.gitignore` корректен.

**Новые находки (2)**:
- LOW `runner.py` — ленивый импорт `json` в теле функции
- LOW `gatherer.py` — дублирование логики сборки между `dry_run` и `collect`

**Тренд**: проект последовательно закрывает весь технический долг. За 5 релизов (v0.7.1 → v0.9.3) исправлены 15 из 15 реальных находок трёх аудитов. Новые находки — исключительно косметические LOW. Проект стабилизировался и готов к стабильному релизу.

---

## Вердикт

**Проект готов к v1.0.0.** 0 CRITICAL, 0 HIGH, 0 MEDIUM, 2 LOW (косметика).

Все реальные находки предыдущих аудитов исправлены. Кодовая база чистая, архитектура консистентна, тесты стабильны и изолированы. Безопасность на высоком уровне: sandbox для внешних команд, валидация piped-команд, dry-run с интерактивным подтверждением, аудит-лог.

Две новые LOW находки — косметические улучшения, не влияющие на работоспособность:
- Вынести `import json` на верхний уровень в `runner.py`
- Рассмотреть дедупликацию логики сборки контента между `dry_run` и `collect`

**Рекомендация**: публиковать v1.0.0 на PyPI. LOW находки можно исправить в v1.0.1 или v1.1.0.

**Что изменилось с v0.9.1**:
- MEDIUM `_cmd_validate`: исправлено — теперь использует `get_profile()` консистентно с остальным кодом
- LOW `cache.py` и `gitignore.py`: добавлены комментарии к магическим числам
- LOW `gitignore.py`: `ValueError` от `relative_to` обрабатывается во всех вызовах
- LOW `tests/runner`: `MagicMock` заменён на `subprocess.CompletedProcess`
- Все 5 реальных находок предыдущего аудита закрыты
- 0 новых проблем безопасности или архитектуры
- Проект находится в лучшем состоянии за всю историю аудитов
