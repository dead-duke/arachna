# Аудит: arachna v1.2.0

**Дата**: 2026-05-31
**Контекст**: полный исходный код (19 модулей + __main__), 33 тестовых файла, llm_docs/TODO.md, CHANGELOG.md v0.1.0–v1.2.0, предыдущий AUDIT_REPORT.md (v0.9.4), .arachna.json, pyproject.toml, README.md, Makefile, LICENSE, requirements-dev.txt, .pre-commit-config.yaml, .github/workflows/test.yml.
**Предыдущий аудит**: 2026-05-29 (v0.9.4), 0 находок — проект был в идеальном состоянии.
**Метод**: полный аудит с нуля. Безопасность → архитектура → тестопригодность.

---

## Сводка

| Уровень   | Количество | Области                               |
|-----------|------------|----------------------------------------|
| CRITICAL  | 0          | —                                      |
| HIGH      | 1          | Архитектура (1)                        |
| MEDIUM    | 1          | Безопасность (1)                       |
| LOW       | 2          | Архитектура (1), тестопригодность (1)  |

**Из предыдущего аудита (v0.9.4)**: 0 находок — нечего перепроверять. Проект был в идеальном состоянии.

**Новые находки (4) — все связаны с новым кодом (presets.py и зависимые модули)**:
- HIGH `presets.py`: `importlib.import_module` вызывается без ограничения пути — пользовательский `presets.json` в сочетании с `tokenizer: "module:func"` или `--preset` из недоверенного источника может привести к импорту произвольного модуля
- MEDIUM `presets.py:175-177`: `detect_presets` с явным `preset_name` не проверяет существование файлов/директорий для этого пресета — возвращает пресет даже если проект не содержит соответствующих файлов, что ломает `--init --defaults --preset godot` на пустом проекте
- LOW `init.py:33-36`: `run_defaults` и `run_interactive` принимают `preset` параметр, но `run_interactive` игнорирует его при автоопределении — `--preset` работает только с `--defaults`
- LOW `tests/presets/test_presets.py`: тесты `detect_presets` и `preset_to_profile` не проверяют внешние пресеты с параметром `preset_name`

**Сильные стороны, которые нельзя ломать**:
- Полный DI токенизатора — ни одной глобальной переменной, всё через параметры функций
- Атомарная запись кэша и манифеста — `tempfile.mkstemp + os.replace`, с fallback при ошибке tempfile
- Валидация команд — piped-команды проверяются по частям, shell-метасимволы обрабатываются, dry-run с интерактивным подтверждением
- Тесты на `tmp_path + monkeypatch` — полная изоляция, параллельный запуск возможен
- `_handle_single` — бинарный поиск с токенизатором для точного усечения
- Кроссплатформенные тесты — `time.sleep(0.01)` для mtime, `skipIf win32` для chmod, `S_IXUSR` только на Unix
- `_assemble_content` — дедуплицированный pipeline сборки контента
- Консистентные импорты — `json` на верхнем уровне во всех модулях
- GitHub Actions CI — матрица 3 OS × 4 Python, lint + test
- 16 пресетов с автоопределением — покрытие Python, JS, Godot, Unity, C/C++, C#, Swift, Kotlin/Java, Ruby, PHP, Docker, Terraform + service-пресеты

**Вердикт**: проект в хорошем состоянии, но новый код (presets.py) добавил 4 находки. Одна HIGH — `importlib` без sandbox-валидации, одна MEDIUM — баг `--preset` с автоопределением, две LOW — неконсистентность CLI и неполное покрытие тестами.

**С чего начать**:
1. HIGH-01 — sandbox-валидация `importlib.import_module` в `tokenizer.py`: ограничить импорт только предустановленными модулями или проверять путь
2. MEDIUM-01 — `detect_presets(preset_name="godot")` должен проверять что проект действительно содержит файлы Godot (сейчас возвращает пресет без проверки)
3. LOW-01 — `run_interactive` с `--preset godot` должен фильтровать автоопределение до указанного пресета
4. LOW-02 — добавить тесты на `detect_presets` и `preset_to_profile` с внешними пресетами и `preset_name`

---

## Безопасность

### [HIGH] src/arachna/presets.py + tokenizer.py — неограниченный importlib.import_module через внешний presets.json

**Статус**: новая находка.
**Файлы**: `presets.py:264 (get_all_presets) → presets.py:163 (detect_presets) → init.py:33 (run_defaults) + tokenizer.py:40 (load_tokenizer)`.
**Суть**: цепочка атаки через недоверенный `presets.json`:

1. `presets.py:264` — `get_all_presets` загружает внешний `presets.json` через `load_presets_from_file(DEFAULT_PRESETS_PATH)`
2. `DEFAULT_PRESETS_PATH = "presets.json"` — это файл в текущей директории
3. `presets.py:128` — `load_presets_from_file` валидирует `split_mode` и `max_tokens`, но не проверяет `tokenizer` на безопасность
4. Пользовательский `presets.json` может указать `"tokenizer": "os:system"` или `"tokenizer": "subprocess:check_output"`
5. `tokenizer.py:40` — `load_tokenizer(spec)` вызывает `importlib.import_module(module_name)` без sandbox-валидации
6. `init.py:33` — `run_defaults` вызывает `detect_presets` → `preset_to_profile`, который копирует `tokenizer` в профиль

При следующем запуске `arachna --all` токенизатор вызовет `importlib.import_module("os")` и затем `os.system(...)`.

**Влияние сейчас**: пользователь должен явно создать вредоносный `presets.json` и запустить `arachna --init --defaults`, затем `arachna --all`. Это не RCE через клонирование репозитория — злоумышленник не может подсунуть `presets.json` удалённо.

**Риск при росте**: при добавлении `--presets-url` или `--presets-path` с удалённой загрузкой — RCE через недоверенный URL. При интеграции с IDE — пользователь может открыть чужой проект с вредоносным `presets.json`, и `arachna --init --defaults` создаст профиль с вредоносным токенизатором.

**Исправление**: в `tokenizer.py:load_tokenizer` добавить sandbox-валидацию:
- Разрешить только предустановленные токенизаторы (`tiktoken`, `transformers`) и пользовательские модули из безопасных путей (например, только из директории проекта)
- Или добавить `--allow-custom-tokenizer` флаг, по умолчанию запретить произвольные импорты
- Минимально: валидировать `tokenizer` в `load_presets_from_file` — запретить `tokenizer` во внешних пресетах, если он не в белом списке

    Python:
    # В load_presets_from_file, после валидации max_tokens:
    tokenizer = preset.get("tokenizer", "default")
    if tokenizer != "default" and not _is_safe_tokenizer(tokenizer):
        print(f"Warning: preset '{name}' has unsafe tokenizer '{tokenizer}', using default")
        preset["tokenizer"] = "default"

---

### Runner (sandbox)

Состояние безопасности runner — отличное, без изменений с v0.9.4.

- Команды без shell-метасимволов выполняются через `shlex.split` → `subprocess.run` без `shell=True`
- `_ALLOWED_COMMANDS` — закрытый список безопасных утилит
- `_BLOCKED_PATTERNS` — блокировка опасных команд
- Piped-команды проверяются по частям
- `allow_dangerous`, `interactive`, `dry_run` — все режимы безопасны
- Аудит-лог в `.arachna_commands.log`

**Нет уязвимостей в runner.**

### CLI

- `--version` обрабатывается до argparse — без риска конфликта с `mutually_exclusive_group`
- `--completion` обрабатывается до argparse
- `--preset` передаётся в `run_defaults`/`run_interactive` — без риска инъекции

### Config

- `.arachna.json` — только JSON
- Валидация профилей через `get_profile()` + `setdefault`
- `DEFAULT_EXCLUDE` генерируется из `_COMMON_EXCLUDE_DIRS`

### File system

- Без изменений с v0.9.4 — проверка размера, обработка ошибок, бинарные файлы

---

## Архитектура

### [MEDIUM] src/arachna/presets.py:175-177 — detect_presets с preset_name не проверяет существование файлов

**Статус**: новая находка.
**Файл**: `presets.py`, строки 175-177.
**Суть**: `detect_presets(preset_name="godot")` немедленно возвращает `["godot"]`, не проверяя что в проекте есть `project.godot`:

    Python:
    if preset_name:
        if preset_name in all_presets:
            return [preset_name]
        print(f"Warning: preset '{preset_name}' not found in built-in or external presets")
        return []

Это приводит к проблеме: `arachna --init --defaults --preset godot` в пустой директории создаст `.arachna.json` с профилем godot, у которого `"directories": ["."]` (пресет godot использует `dirs: ["."]`). `preset_to_profile` фильтрует `dirs` через `_detect_dir`, но `"."` всегда существует, поэтому `directories: ["."]` попадёт в профиль. `patterns: ["*.gd", "*.tscn", "*.tres", "*.gdshader"]` будут искать несуществующие файлы. Профиль будет создан, но `arachna --all` соберёт пустой вывод (нет `.gd` файлов).

Поведение контринтуитивно: пользователь ожидает что `--preset godot` проверит наличие `project.godot`, а не просто создаст профиль в любой директории.

**Влияние сейчас**: `--preset godot` в пустой директории создаёт валидный, но бесполезный профиль. `arachna --all` выводит "No content collected." без ошибки.

**Риск при росте**: пользователи `--presет` ожидают что пресет проверяет совместимость с проектом. При добавлении новых пресетов с нестандартными `dirs` (например, Unreal Engine с `Content/`, `Source/`) поведение станет ещё более запутанным.

**Исправление**: `detect_presets` с явным `preset_name` должен проверять detect-пути пресета:

    Python:
    if preset_name:
        if preset_name not in all_presets:
            print(f"Warning: preset '{preset_name}' not found")
            return []
        preset = all_presets[preset_name]
        detect_paths = preset.get("detect", [])
        if detect_paths and not _detect_any(detect_paths):
            print(f"Warning: preset '{preset_name}' doesn't match this project")
            return []
        return [preset_name]

---

### [LOW] src/arachna/init.py:33-36 — run_interactive игнорирует --preset

**Статус**: новая находка.
**Файл**: `init.py`, строки 33-36.
**Суть**: `run_interactive` принимает параметр `preset`, но передаёт его только в `detect_presets` — который с `preset_name` возвращает список из одного элемента. Дальше `run_interactive` показывает этот пресет и спрашивает подтверждения. Это работает, но семантически неконсистентно: в интерактивном режиме `--preset godot` не отличается от автоопределения Godot-проекта.

Более того, `run_defaults` использует `--preset` чтобы ограничить профили одним пресетом, а `run_interactive` всё равно показывает все автоопределённые пресеты + указанный (если они пересекаются). При `--preset godot` в Godot-проекте `detect_presets` вернёт `["godot"]`, но это потому что `preset_name` переопределяет автоопределение, а не потому что `run_interactive` фильтрует.

**Влияние сейчас**: минимальное. `--preset` в интерактивном режиме работает корректно (показывает только указанный пресет), но недокументирован и поведение неочевидно.

**Риск при росте**: при добавлении `--preset` в документацию пользователи будут ожидать одинакового поведения в `--defaults` и интерактивном режиме.

**Исправление**: либо явно запретить `--preset` без `--defaults` (добавить проверку в `__main__.py`), либо документировать что `--preset` работает только с `--defaults`.

---

### Поток данных (без изменений)

    CLI (__main__.py)
      → _run_profile → get_profile (config.py)
        → dry_run (gatherer.py) → _assemble_content → render_dry_run (renderer.py)
        → collect (collector.py) → _assemble_content → splitter.py → запись файлов

Новый поток для `--init`:

    CLI (__main__.py) --init
      → run_defaults / run_interactive (init.py)
        → detect_presets (presets.py) → автоопределение или явный preset_name
        → preset_to_profile (presets.py) → профили
      → _write_config → .arachna.json

### Зоны ответственности (новые)

- `presets.py` — 16 встроенных пресетов, автоопределение, загрузка внешних `presets.json`, валидация, конвертация в профили

---

## Тестопригодность

### [LOW] tests/presets/test_presets.py — неполное покрытие внешних пресетов с preset_name

**Статус**: новая находка.
**Файл**: `tests/presets/test_presets.py`.
**Суть**: тесты покрывают:
- `detect_presets()` без аргументов (автоопределение) — 16 тестов
- `detect_presets(preset_name="godot")` — 3 теста (explicit, unknown, override)
- `preset_to_profile("python")` — 3 теста
- `load_presets_from_file` — 8 тестов
- `get_all_presets` — 3 теста
- `detect_presets` с внешними пресетами — 1 тест

Но нет тестов на:
- `detect_presets(preset_name="my_game", external_path=...)` — явный пресет из внешнего файла
- `preset_to_profile("my_game", external_path=...)` — профиль из внешнего пресета
- `detect_presets(preset_name="godot")` на проекте без `project.godot` (связано с MEDIUM находкой)

**Влияние сейчас**: основные сценарии покрыты, но edge cases с внешними пресетами и явным `preset_name` не проверены.

**Риск при росте**: при добавлении новых функций в `presets.py` (например, `--presets-url`) отсутствие тестов на комбинацию внешних пресетов и явного `preset_name` может скрыть баги.

**Исправление**: добавить тесты:
- `test_detect_presets_explicit_external` — явный пресет из внешнего `presets.json`
- `test_preset_to_profile_external_with_name` — профиль из внешнего пресета по имени
- `test_detect_presets_explicit_no_match` — `preset_name` для пресета, чьи detect-пути не найдены (после исправления MEDIUM)

### Инфраструктура тестов (улучшения с v0.9.4)

- 33 тестовых файла (был 31, +2: `tests/presets/test_presets.py`, тесты init расширены)
- GitHub Actions CI: матрица 3 OS × 4 Python = 12 jobs, lint + test
- Кроссплатформенные фиксы: `time.sleep(0.01)` для mtime, `skipIf win32` для chmod, `S_IXUSR` только на Unix
- `_make_entry` в cache-тестах использует реальный SHA256 вместо `"dummy"`
- `.pre-commit-config.yaml`: ruff + pytest при каждом коммите

### Покрытие (новое)

- `presets.py`: `_detect_dir`, `_detect_file`, `_detect_any`, `detect_presets` (16 языков/движков + service-пресеты), `preset_to_profile` (python, git, docker, unknown, filters missing), `load_presets_from_file` (valid, not found, invalid json, not object, non-dict preset, invalid split_mode, zero/negative max_tokens, unknown keys, non-list fields), `get_all_presets` (builtin, merged, default path), `detect_presets` с external
- `init.py`: все тесты обновлены под `detect_presets` mock, добавлены `test_run_defaults_detects_godot`, `test_run_defaults_detects_docker`, `test_run_interactive_decline_profile`, `test_run_interactive_existing_config_overwrite`, `test_run_interactive_existing_config_abort`

---

## Сравнение с предыдущим аудитом (v0.9.4)

**Предыдущий аудит**: 0 находок. Проект был в идеальном состоянии.

**Новые находки (4)** — все связаны с новым кодом:
- HIGH: `importlib` без sandbox-валидации (presets.py + tokenizer.py)
- MEDIUM: `detect_presets` с `preset_name` не проверяет существование файлов
- LOW: `run_interactive` игнорирует `--preset`
- LOW: тесты на внешние пресеты с `preset_name`

**Исправлено из предыдущего (0)**: нечего было исправлять.

**Тренд**: проект активно развивается — 3 новых релиза (v1.0.0 → v1.2.0), 16 пресетов, внешние `presets.json`, GitHub Actions CI, кроссплатформенные тесты. Новый код добавляет функциональность, но вместе с ней и новые находки — это нормально для активной фазы развития. Все находки — в новом коде, старый код остаётся чистым.

---

## Вердикт

**Проект в хорошем состоянии, но требует sandbox-валидации для `importlib`.** 1 HIGH, 1 MEDIUM, 2 LOW.

Старый код (v0.9.4 и ранее) остаётся чистым — 0 находок. Новый код (v1.1.0–v1.2.0, presets.py + связанные изменения) добавил 4 находки. Это нормально для фазы активного роста.

HIGH находка — `importlib.import_module` без sandbox-валидации. Сейчас неэксплуатируема удалённо, но создаёт риск при добавлении функций загрузки пресетов по URL или интеграции с IDE.

MEDIUM находка — баг `--preset godot` в пустой директории. Контринтуитивное поведение, но не ломает работу.

**Рекомендация**: исправить HIGH и MEDIUM до v1.3.0. LOW можно отложить.

**История аудитов**:
- v0.8.5: 6 находок (3 MEDIUM, 3 LOW) — закрыты в v0.9.2–v0.9.3
- v0.9.1: 6 находок (3 MEDIUM, 3 LOW, 5 реальных) — закрыты в v0.9.3
- v0.9.3: 2 находки (2 LOW) — закрыты в v0.9.4
- v0.9.4: 0 находок — чисто
- v1.2.0: 4 находки (1 HIGH, 1 MEDIUM, 2 LOW) — все в новом коде presets.py
