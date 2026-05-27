# TODO

## Текущий цикл — 2026-05-25, источник: аудит v0.5.0

### [HIGH] src/arachna/cache.py — состояние гонки в инкрементальном режиме
- [x] Источник: Архитектура / HIGH + Аудит H-01
- [x] Версия: v0.6.1
- [x] Суть: save_cache делает write_text без атомарности — краш во время записи оставит повреждённый JSON. Между get_changed_files и update_cache файл может измениться.
- [x] Решение: атомарная запись через tempfile + os.replace; рассмотреть хэш содержимого вместо mtime для детекта изменений.

### [HIGH] src/arachna/gitignore.py — ограничение размера .gitignore
- [x] Источник: Безопасность / MEDIUM + Аудит M-01
- [x] Версия: v0.6.1
- [x] Суть: load_gitignore_patterns читает все .gitignore рекурсивно без ограничения размера → DoS через исчерпание памяти. Также жёстко закодированный список исключаемых директорий (venv, node_modules, __pycache__, .) неполон — отсутствуют .tox, .mypy_cache, .pytest_cache.
- [x] Решение: добавить проверку file size до чтения (пропускать > 100 КБ); расширить список исключаемых директорий (EXCLUDED_DIRS) и вынести его в константу для переиспользования в config.py.

### [MEDIUM] src/arachna/formatter.py — проверка размера бинарных файлов до read_text()
- [x] Источник: Безопасность / MEDIUM
- [x] Версия: v0.6.1
- [x] Суть: format_file_section вызывает read_text() до проверки _is_binary_allowed. Большой бинарный файл вызывает MemoryError.
- [x] Решение: перенести проверку размера (и расширения) до попытки read_text().

### [LOW] src/arachna/splitter.py — вынести константу CHARS_PER_TOKEN
- [ ] Источник: Архитектура / LOW
- [ ] Версия: v0.6.1
- [ ] Суть: max_chars = max_tokens * 4 в splitter.py неявно связано с константой 4 в tokenizer.py. Изменение tokenizer сломает truncation-logic.
- [ ] Решение: вынести CHARS_PER_TOKEN = 4 в tokenizer.py, импортировать в splitter.py.

### [HIGH] src/arachna/runner.py — sandbox-валидация команд и аудит-лог
- [x] Источник: Безопасность / HIGH + Аудит H-02
- [x] Версия: v0.7.0
- [x] Суть: shell=True для команд из конфига — риск RCE через вредоносный .arachna.json. Отсутствует журнал исполненных команд — невозможен аудит инцидента.
- [x] Решение: добавить валидацию команд (allowlist безопасных утилит, запрет curl/wget и т.п.) или запрос подтверждения у пользователя при первом запуске профиля; добавить logging выполняемых команд (--log-commands или всегда в verbose); возможно — хэш-подпись доверенных конфигов.

### [HIGH] src/arachna/__main__.py — рефакторинг main() и устранение дублирования _cmd_all/_cmd_single
- [x] Источник: Архитектура / HIGH + MEDIUM
- [x] Версия: v0.7.0
- [x] Суть: main() нарушает SRP (84 строки); _cmd_all и _cmd_single дублируют логику get_profile + compress + format + collect.
- [x] Решение: вынести роутинг команд в отдельный dispatcher; объединить _cmd_all и _cmd_single через общую _run_profile(); добавить обработчик --version.

### [MEDIUM] src/arachna/gatherer.py — устранить глобальное состояние _TOKENIZE и декомпозировать _collect_named_sections
- [ ] Источник: Архитектура / MEDIUM + Тесты / MEDIUM + Аудит M-02
- [ ] Версия: v0.7.0
- [ ] Суть: set_tokenizer меняет модульную переменную — побочный эффект для тестов и риск при использовании как библиотеки; _collect_named_sections — God function на 47 строк; splitter.py импортирует count_tokens напрямую, минуя глобальный state — несогласованность: splitter всегда использует дефолтный токенизатор.
- [ ] Решение: передавать tokenizer через параметры (dependency injection) во все модули; разбить _collect_named_sections на _collect_pre_commands, _scan_directories, _read_files; пробросить tokenizer в splitter.

### [MEDIUM] src/arachna/formatter.py — вынести импорт json на уровень модуля
- [x] Источник: Архитектура / MEDIUM
- [x] Версия: v0.7.0
- [x] Суть: import json as _json внутри _format_json и _format_binary — индикатор неоптимальной организации.
- [x] Решение: вынести import json в начало файла; рассмотреть выделение binary-форматтера в отдельный модуль formatter_binary.py.

### [MEDIUM] src/arachna/config.py — унифицировать exclude-паттерны с gitignore.py
- [ ] Источник: Архитектура / LOW
- [ ] Версия: v0.7.0
- [ ] Суть: DEFAULT_EXCLUDE и gitignore.py дублируют исключения (venv, node_modules, __pycache__). Двойная фильтрация усложняет понимание.
- [ ] Решение: вынести список "всегда исключаемых" директорий в константу EXCLUDED_DIRS, использовать в обоих модулях.

### [MEDIUM] src/arachna/renderer.py — вынести магические значения в константы
- [ ] Источник: Архитектура / LOW
- [ ] Версия: v0.7.0
- [ ] Суть: порог 0.05 для <0.1%, строка "<0.1%" — магические значения без пояснения семантики.
- [ ] Решение: вынести в именованные константы MIN_PCT_THRESHOLD, MIN_PCT_DISPLAY с документирующими комментариями.

### [MEDIUM] src/arachna/collector.py — атомарная запись манифеста
- [ ] Источник: Архитектура / HIGH + Аудит H-01
- [ ] Версия: v0.7.0
- [ ] Суть: save_manifest делает write_text без атомарности; _cmd_single вызывает clean_manifest → collect → save_manifest — три раздельных операции без блокировок, возможна гонка при параллельных запусках.
- [ ] Решение: атомарная запись через tempfile + os.replace; добавить filelock для операций с манифестом.

### [MEDIUM] src/arachna/splitter.py — флаг truncated в _handle_single
- [ ] Источник: Архитектура / Аудит M-03
- [ ] Версия: v0.7.0
- [ ] Суть: _handle_single обрезает текст необратимо, без признака truncated и без информации сколько контента потеряно. Вызывающий код не узнает что контент был обрезан.
- [ ] Решение: возвращать (text, was_truncated) или добавить маркер в выходной текст с информацией о потерянных токенах; логировать truncation в collector.

### [MEDIUM] tests/ — заменить os.chdir на tmp_path/monkeypatch
- [ ] Источник: Тесты / MEDIUM + Аудит M-04
- [ ] Версия: v0.7.0
- [ ] Суть: os.chdir в тестах делает невозможным параллельный запуск (pytest-xdist). Тесты collector, config, gatherer зависят от глобального состояния cwd. Одновременное использование os.chdir и patch('pathlib.Path.cwd') избыточно.
- [ ] Решение: перевести тесты на tmp_path (pytest fixture) + monkeypatch.chdir; изолировать тесты tokenizer от глобального _TOKENIZE; удалить двойное патчение cwd.

### Отложено
- src/arachna/completion.py — heredoc-тесты на shell-совместимость: требует запуска в реальной оболочке, не блокирует v0.7.0
- tests/main/*.py — каскадные CLI-тесты: будут упрощены после рефакторинга main.py (v0.7.0)
- tests/config/test_get_profile.py — изоляция от родительского .arachna.json: закроется после перехода на tmp_path в v0.7.0
- src/arachna/cache.py — изолируемое имя файла кэша: требуется product-решение о хранении кэша в output_dir
- tests/runner/test_run_command.py — зависимость от echo: критично только для Windows CI

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
- [x] .arachna.json: "all" profile (32768 tokens)
- [x] 175 tests, 90% coverage

## v0.6.0 — Pluggable tokenizer
- [x] load_tokenizer(spec) in tokenizer.py
- [x] tokenizer field in profile (default: "default")
- [x] Plumbed through collector → gatherer → splitter
- [x] Tests for custom tokenizer plugin
- [x] 179 tests, 90% coverage

## v0.7.0 — Additional tests
- [ ] Coverage ≥ 95%
- [ ] Integration tests for --format xml/json output
- [ ] Edge cases: empty files, huge files, symlinks

## v1.0.0 — Public release
- [ ] pip install arachna (publish to PyPI)
- [ ] arachna install-hook (git post-commit)

## Backlog
- [ ] CI/CD (GitHub Actions)
