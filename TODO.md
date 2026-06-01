# TODO

## v1.4.0 — Security hardening + cleanup
- [ ] tokenizer.py: убрать fallback на sys.modules в _is_safe_tokenizer
- [ ] runner.py: убрать chmod, chown из _ALLOWED_COMMANDS
- [ ] gatherer.py: проверка is_symlink() в _scan_directories
- [ ] __main__.py: --version на argparse action='version'
- [ ] gatherer.py: декомпозиция _assemble_content
- [ ] tests/runner: покрытие аудит-лога
- [ ] tests/presets: убрать дублирование тестов
- [ ] Бамп __version__ до 1.4.0

## Backlog
- [ ] Unreal Engine пресет
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
