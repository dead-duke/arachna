"""Execution subpackage — command running, content splitting, gitignore parsing."""

from .gitignore import (
    load_gitignore_patterns,
)
from .runner import (
    _ALLOWED_COMMANDS,
    _SHELL_CHARS,
    _is_safe_command,
    _sanitize_log,
    _validate_command,
    run_command,
    run_pre_commands,
)
from .splitter import (
    _SIG_EXTRACTORS,
    _handle_single,
    _split_oversized_section,
    _split_to_sections,
    extract_signatures,
    pack_into_parts,
    split,
    split_sections,
)
from .splitter import (
    C_LIKE_LANGS as _SPLITTER_C_LIKE_LANGS,
)
from .splitter import (
    SCRIPT_LANGS as _SPLITTER_SCRIPT_LANGS,
)

__all__ = [
    "_ALLOWED_COMMANDS",
    "_SHELL_CHARS",
    "_SIG_EXTRACTORS",
    "_SPLITTER_C_LIKE_LANGS",
    "_SPLITTER_SCRIPT_LANGS",
    "_handle_single",
    "_is_safe_command",
    "_sanitize_log",
    "_split_oversized_section",
    "_split_to_sections",
    "_validate_command",
    "extract_signatures",
    "load_gitignore_patterns",
    "pack_into_parts",
    "run_command",
    "run_pre_commands",
    "split",
    "split_sections",
]
