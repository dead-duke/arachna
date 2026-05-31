# TODO

## v1.0.1 — Windows test fixes
- [x] tests/cache: _make_entry с реальным хешем вместо "dummy"
- [x] tests/cache: time.sleep(0.01) в test_get_changed_files_modified и test_get_changed_files_mixed
- [x] tests/formatter: test_permission_denied — skip на Windows (chmod 0o000 не работает)
- [x] tests/gatherer: time.sleep(0.01) в test_collect_sections_incremental_detects_modified
- [x] tests/hook: проверка S_IXUSR только на Unix (Windows не поддерживает)
- [x] Бамп __version__ до 1.0.1

## Backlog
- [ ] CI/CD (GitHub Actions)
- [ ] Интеграция в IDE (VS Code extension)
- [ ] Web UI для визуального редактора профилей
