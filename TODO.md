# TODO

## v1.2.1 — Security fix
- [ ] tokenizer.py: sandbox-валидация importlib — запретить произвольные импорты
- [ ] presets.py: валидация tokenizer в load_presets_from_file — запретить unsafe tokenizer во внешних пресетах
- [ ] presets.py: detect_presets с preset_name проверяет detect-пути
- [ ] Бамп __version__ до 1.2.1

## v1.2.2 — CLI consistency
- [ ] init.py: run_interactive фильтрует автоопределение по --preset
- [ ] tests/presets: тесты на внешние пресеты с preset_name

## Backlog
- [ ] Unreal Engine пресет
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
