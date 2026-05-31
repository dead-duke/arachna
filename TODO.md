# TODO

## v1.2.1 — Security fix
- [x] tokenizer.py: sandbox-валидация importlib — запретить произвольные импорты
- [x] presets.py: валидация tokenizer в load_presets_from_file — запретить unsafe tokenizer во внешних пресетах
- [x] presets.py: detect_presets с preset_name проверяет detect-пути
- [x] Бамп __version__ до 1.2.1

## v1.2.2 — CLI consistency
- [x] init.py: run_interactive фильтрует автоопределение по --preset
- [x] tests/presets: тесты на внешние пресеты с preset_name

## Backlog
- [ ] Unreal Engine пресет
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
