# Аудит: arachna v0.8.5

**Дата**: 2026-05-29
**Контекст**: полный исходный код (18 модулей), тесты, TODO.md, CHANGELOG.md v0.1.0–v0.9.2, старый AUDIT_REPORT.md (v0.7.1), .arachna.json, pyproject.toml.
**Предыдущий аудит**: 2026-05-28 (v0.7.1), 7 находок (2 HIGH, 2 MEDIUM, 3 LOW).
**Метод**: полный аудит с нуля. Безопасность → архитектура → тестопригодность.

---

## Сводка

| Уровень   | Количество | Области                               |
|-----------|------------|----------------------------------------|
| CRITICAL  | 0          | —                                      |
| HIGH      | 0          | —                                      |
| MEDIUM    | 3          | Архитектура (2), тестопригодность (1)  |
| LOW       | 3          | Архитектура (2), документация (1)      |

**Из предыдущего аудита (v0.7.1) исправлено (7 из 7)**:
- ✅ HIGH `_resolve_command` — теперь `_validate_command` разбирает piped-команды по `|` и проверяет каждую часть отдельно. `_resolve_base` вместо `_resolve_command`. Тесты подтверждают: `test_validate_command_pipe_safe`, `test_validate_command_pipe_unknown`.
- ✅ HIGH `was_truncated` в `split()` — теперь `logger.warning` вместо `print`. Библиотечный пользователь может перехватить через logging.
- ✅ MEDIUM `shlex.split` — проверка `if not cmd.strip(): return ""` до `shlex.split`. `ValueError` от `shlex.split` перехватывается отдельно с логированием. Тест `test_shlex_value_error`.
- ✅ MEDIUM `_collect_named_sections` — декомпозирована. `_collect_directory_sections` и `_collect_file_sections` выделены. `_collect_named_sections` теперь 20 строк вместо 58.
- ✅ LOW `DEFAULT_EXCLUDE` — генерируется из `_COMMON_EXCLUDE_DIRS` программно. Цикл `for _d in sorted(_COMMON_EXCLUDE_DIRS): DEFAULT_EXCLUDE.extend([_d, f"{_d}/*"])`.
- ✅ LOW тесты splitter — добавлены `test_custom_tokenizer_called`, `test_custom_tokenizer_small_limit`, `test_custom_tokenizer_by_file`, `test_custom_tokenizer_single`, `test_custom_tokenizer_by_paragraph`. Все с `MagicMock` и проверкой `.called`.
- ✅ LOW `CHARS_PER_TOKEN` — `_handle_single` больше не использует `CHARS_PER_TOKEN`. Усечение через бинарный поиск с токенизатором (строки 112-121). Тест `test_single_truncation` по-прежнему проверяет наличие "truncated".

**Новые находки (6)**:
- MEDIUM `hook.py`: `install_hook` не проверяет `.git` на директорию — только на существование (может быть файлом)
- MEDIUM `doctor.py`: `run_doctor` не проверяет `.gitignore` на существование перед `load_gitignore_patterns`
- MEDIUM тесты `doctor` замоканы на `sys.exit` через `print_doctor` — не проверяют `sys.exit(1)` при ошибках
- LOW `__main__.py`: `_cmd_doctor` и `_cmd_install_hook` не используют `config` параметр, хотя принимают его
- LOW CHANGELOG: v0.7.4, v0.7.5, v0.8.0–v0.8.5 отсутствуют в CHANGELOG.md (версии есть в TODO.md)
- LOW `.gitignore` содержит `/llm_docs` — директория с аудитами исключена из репозитория, но полезна для отслеживания

**Сильные стороны, которые нельзя ломать**:
- Полный DI токенизатора — ни одной глобальной переменной, всё через параметры
- Атомарная запись кэша и манифеста — `tempfile + os.replace`, без fallback
- Валидация команд — piped-команды проверяются по частям, shell-метасимволы обрабатываются
- Тесты на `tmp_path + monkeypatch` — параллельный запуск возможен
- `_handle_single` — бинарный поиск с токенизатором для точного усечения
- Coverage — тесты покрывают edge cases (cache fallback, unclosed quotes, interactive tty, dry-run)

**Вердикт**: проект в отличном состоянии. 0 CRITICAL, 0 HIGH. Все находки предыдущего аудита исправлены. Три MEDIUM — локальные недочёты в новых модулях, не влияющие на безопасность. Три LOW — косметика и документация. Проект готов к v1.0.0.

**С чего начать**:
1. MEDIUM-01 — проверка `.git` на директорию в `hook.py`
2. MEDIUM-02 — обработка отсутствия `.gitignore` в `doctor.py`
3. LOW — синхронизировать CHANGELOG с версиями 0.7.4–0.8.5

---

## Архитектура

### [MEDIUM] src/arachna/hook.py:33 — install_hook не проверяет что .git — директория

**Статус**: новая находка.
**Суть**: `install_hook()` на строке 33 проверяет:

    git_dir = cwd / ".git"
    if not git_dir.exists():
        return False, "Not a git repository (.git not found)"

`Path.exists()` возвращает `True` и для файла, и для директории. Если в корне проекта лежит файл `.git` (например, `git init` не выполнялся, файл создан вручную), проверка пройдёт, но `git_dir / "hooks"` создаст директорию `hooks` рядом с файлом `.git`, а не внутри git-репозитория.

**Влияние сейчас**: маргинальное. Файл `.git` вместо директории — экзотический случай.

**Риск при росте**: при использовании `arachna install-hook` в скриптах инициализации проекта — hook установится в неправильное место, не будет выполняться после коммита. Пользователь не получит ошибки.

**Исправление**: заменить `git_dir.exists()` на `git_dir.is_dir()`.

    Python:
    if not git_dir.is_dir():
        return False, "Not a git repository (.git directory not found)"

---

### [MEDIUM] src/arachna/doctor.py:48 — run_doctor падает при отсутствии .gitignore

**Статус**: новая находка.
**Суть**: `run_doctor()` на строках 47-52:

    try:
        patterns = load_gitignore_patterns(project_root)
        if patterns:
            result["gitignore"].append(f"Loaded {len(patterns)} gitignore patterns")
    except OSError as e:
        result["gitignore"].append(f"Error loading .gitignore: {e}")

`load_gitignore_patterns()` внутри делает `root.rglob(".gitignore")`. Если `project_root` не существует или недоступен, `rglob` выбросит `OSError`. Но если `project_root` существует, а `.gitignore` нет — это не ошибка, `rglob` вернёт пустой итератор. Однако если `project_root` — путь к файлу или удалённой директории, `rglob` упадёт. `run_doctor` может быть вызван с `project_root` из CLI-аргументов.

Кроме того, `load_gitignore_patterns` внутри делает `gitignore_path.parent.relative_to(root)` — если `gitignore_path` находится вне `root` (симлинки), будет `ValueError`, который не перехватывается ни в `load_gitignore_patterns`, ни в `run_doctor`.

**Влияние сейчас**: низкое. `run_doctor` вызывается без аргументов из CLI, `project_root = Path.cwd()` всегда существует.

**Риск при росте**: при использовании `run_doctor` как библиотеки с произвольным `project_root` — возможно падение.

**Исправление**: добавить проверку `project_root.is_dir()` перед `load_gitignore_patterns`. В `load_gitignore_patterns` добавить обработку `ValueError` для `relative_to`.

---

### [MEDIUM] tests/doctor/test_doctor.py — тесты не проверяют exit code при ошибках

**Статус**: новая находка.
**Суть**: тесты `test_doctor` проверяют `run_doctor()` и `print_doctor()`, но не тестируют `_cmd_doctor` из `__main__.py`. Функция `_cmd_doctor` вызывает `sys.exit(1)` при ошибках, но это не покрыто тестами. Аналогично `_cmd_install_hook`.

**Влияние сейчас**: `sys.exit` в CLI-командах не протестирован. Рефакторинг `_cmd_doctor` может сломать exit code, и тесты не заметят.

**Риск при росте**: CI/CD, полагающийся на exit code (`arachna --doctor && echo ok`), не получит ожидаемого поведения.

**Исправление**: добавить тесты на `_cmd_doctor` и `_cmd_install_hook` с проверкой `sys.exit`.

---

## Низкоприоритетные находки

### [LOW] src/arachna/__main__.py:179-186 — _cmd_doctor и _cmd_install_hook принимают неиспользуемые параметры

**Статус**: новая находка.
**Суть**: `_cmd_doctor(config)` на строке 179 принимает `config`, но не использует его — `run_doctor()` сам вызывает `load_config()`. Аналогично `_cmd_install_hook(args)` на строке 185 принимает `args`, но использует только `args.force`. Сигнатуры сбивают с толку.

**Влияние сейчас**: никакого. Работает корректно.

**Риск при росте**: при рефакторинге кто-то может начать передавать `config` в `run_doctor` и ожидать что он будет использован. Несоответствие сигнатуры и тела — источник багов.

**Исправление**: либо передавать `config` в `run_doctor`, либо убрать параметр из сигнатуры.

---

### [LOW] CHANGELOG.md — отсутствуют версии v0.7.4, v0.7.5, v0.8.0–v0.8.5

**Статус**: новая находка.
**Суть**: CHANGELOG содержит записи до v0.7.4, но версии v0.7.5, v0.8.0–v0.8.5 (из TODO.md) отсутствуют. TODO.md утверждает что они выполнены, CHANGELOG — нет. Это создаёт путаницу при публикации.

**Влияние сейчас**: пользователи видят последнюю версию v0.7.4 в CHANGELOG, хотя код на v0.8.5.

**Риск при росте**: при публикации v1.0.0 никто не узнает что было сделано в 6 минорных версиях.

**Исправление**: добавить записи v0.7.5, v0.8.0–v0.8.5 в CHANGELOG перед v1.0.0.

---

### [LOW] .gitignore — /llm_docs исключена из репозитория

**Статус**: новая находка.
**Суть**: `.gitignore` содержит `/llm_docs` — директория с аудитами исключена из git. Это означает что история аудитов не версионируется. При работе с аудитором это нормально (результаты в файловой системе), но при передаче проекта другому разработчику история принятия архитектурных решений теряется.

**Влияние сейчас**: при работе через прокси-консоль — допустимо.

**Риск при росте**: новый разработчик не увидит историю аудитов и может повторить старые ошибки.

**Исправление**: убрать `/llm_docs` из `.gitignore` или закомментировать с пояснением.

---

## Сравнение с предыдущим аудитом (v0.7.1)

**Предыдущий аудит**: 7 находок (2 HIGH, 2 MEDIUM, 3 LOW).

**Исправлено (7 из 7)** — беспрецедентно. Все находки закрыты:
- HIGH `_resolve_command` для piped-команд — исправлено через `_validate_command` с разбором по `|`
- HIGH `was_truncated` теряется в API — исправлено через `logger.warning`
- MEDIUM `shlex.split` без проверки — исправлено
- MEDIUM God function — декомпозирована
- LOW `DEFAULT_EXCLUDE` — генерируется из `_COMMON_EXCLUDE_DIRS`
- LOW тесты splitter — добавлены тесты с `MagicMock`
- LOW `CHARS_PER_TOKEN` — заменён на бинарный поиск с токенизатором

**Новые находки (6)** — все MEDIUM/LOW, относятся к новым модулям (doctor, hook) и документации.

**Тренд**: проект последовательно закрывает технический долг. За три релиза (v0.7.1 → v0.8.5) исправлены все находки двух аудитов. Новые модули добавляются с хорошим покрытием тестов, но с мелкими архитектурными недочётами.

---

## Состояние тестов

- Количество тестов выросло (добавлены doctor, hook, edge cases в cache/formatter/collector/runner/splitter)
- Все тесты на `tmp_path + monkeypatch` — параллельный запуск возможен
- Тесты runner покрывают dry-run, interactive tty, piped-команды, `shlex` errors
- Тесты splitter проверяют проброс кастомного токенизатора через `MagicMock`
- Тесты collector проверяют merge mode, `_find_next_part_num`, post_commands
- Тесты cache проверяют fallback при ошибке tempfile, None hash, missing files
- **Пробел**: нет тестов на `_cmd_doctor` и `_cmd_install_hook` с проверкой `sys.exit`

---

## Вердикт

**Проект готов к v1.0.0.** 0 CRITICAL, 0 HIGH. Все находки двух последовательных аудитов исправлены. Кодовая база в лучшем состоянии за всю историю наблюдений.

Три MEDIUM — локальные недочёты в новых модулях (doctor, hook), не влияющие на основной функционал. Три LOW — косметика и документация. Всё исправимо без архитектурных изменений.

**Рекомендация**: исправить MEDIUM-01 (hook.py: `.git` → `.is_dir()`) и синхронизировать CHANGELOG. Затем публиковать v1.0.0 на PyPI.

**Что изменилось с v0.7.1**:
- Безопасность: piped-команды проверяются по частям, dry-run не выполняет небезопасные команды без подтверждения
- Архитектура: `_collect_named_sections` декомпозирована, `_handle_single` использует точное токенизаторное усечение
- Тестопригодность: coverage расширен на edge cases, кастомные токенизаторы в splitter
- Новые фичи: `--doctor`, `--install-hook`, `--merge`, dry-run sandbox
