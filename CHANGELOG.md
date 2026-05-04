# Changelog

## v0.1.0 — MVP

- tokenizer.py: conservative token count (4 chars ≈ 1 token), no dependencies
- config.py: load .arachna.json, find_config() searches upwards
- collector.py: collect files from directories, specific files, pre_commands, command mode
- Safe command execution: shlex.split() with shell=True fallback for shell metacharacters
- Split modes: by_file (atomic files), by_paragraph, by_marker, single
- exclude_patterns with fnmatch + DEFAULT_EXCLUDE
- CLI: --profile, --all, --clean, --list
- pip install -e . with pyproject.toml
- README with install, usage, config fields, split modes