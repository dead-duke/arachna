"""Config layer — configuration, presets, init, validation, doctor, hook, completion, profiling.

Subpackages:
- core: config loading, profile resolution, validation
- presets: preset detection, validation, remote fetching
- setup: init (interactive/defaults) and git hook installer
"""

from typing import Literal

VALID_SPLIT_MODES = {"by_file", "by_paragraph", "by_marker", "single"}
"""Valid split modes shared across config modules."""

COLLECTION_MODES = {"full", "repo-map", "headers"}
"""Collection strategy modes used by gatherer_strategies.py."""

CollectionMode = Literal["full", "repo-map", "headers"]
OutputFormat = Literal["markdown", "xml", "json"]
SplitMode = Literal["by_file", "by_paragraph", "by_marker", "single"]
