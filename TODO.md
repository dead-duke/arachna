# TODO

## v1.4.0 — Security hardening + cleanup
- [x] tokenizer.py: убрать fallback на sys.modules в _is_safe_tokenizer
- [x] runner.py: убрать chmod, chown из _ALLOWED_COMMANDS
- [x] gatherer.py: проверка is_symlink() в _scan_directories
- [x] __main__.py: --version на argparse action='version'
- [x] gatherer.py: декомпозиция _assemble_content
- [x] tests/runner: покрытие аудит-лога
- [x] tests/presets: убрать дублирование тестов
- [x] Бамп __version__ до 1.4.0

## Backlog
- [ ] Unreal Engine пресет
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
