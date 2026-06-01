# TODO

## v1.4.1 — Unified split + audit fixes
- [x] collector.py: добавить total=total_parts в title_tmpl.format
- [x] LOW: убрать mv и cp из _ALLOWED_COMMANDS
- [x] LOW: проверка detect-путей для service presets с явным preset_name
- [x] LOW: _build_toc — сделать форматно-независимой через named_sections
- [x] LOW: тесты на _build_toc для xml/json форматов
- [x] LOW: вынести логику подсчёта токенов _write_manifest в общую функцию
- [x] LOW: удалить дублирующиеся тесты presets (удалены из test_presets.py)
- [x] gatherer.py: unified split — единый поток секций, плотное заполнение частей
- [x] .arachna.json: убрать pre_split_mode/pre_split_marker из профиля full

## Backlog
- [ ] Unreal Engine пресет
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
