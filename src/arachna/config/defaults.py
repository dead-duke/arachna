"""Default values for arachna configuration.

Single source of truth for all constants that may need tweaking.
Import from here instead of hardcoding in multiple modules.
"""

DEFAULT_PRESETS_URL = "https://raw.githubusercontent.com/dead-duke/arachna/main/presets.json"

_COMMON_EXCLUDE_DIRS = frozenset(
    {
        ".git",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "venv",
        "node_modules",
    }
)

DEFAULT_EXCLUDE = ["*__pycache__*", "*.pyc", "*.egg-info*", ".DS_Store"]
for _d in sorted(_COMMON_EXCLUDE_DIRS):
    DEFAULT_EXCLUDE.extend([_d, f"{_d}/*"])
