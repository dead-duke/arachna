# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Public Collection API.

All functions require an explicit ArachnaConfig. The caller is responsible
for loading the configuration and resolving profile names to ProfileConfig
before calling this API. This keeps the API layer free of config/ dependencies.
"""

import contextlib
from pathlib import Path

from ..config.profile_config import ArachnaConfig, ProfileConfig
from ..domain.api_types import CollectResult
from ..domain.collector import collect as _collect


def collect(
    root: Path,
    profile: ProfileConfig,
    config: ArachnaConfig,
    output_dir: str | None = None,
    query: str | None = None,
    mode: str = "full",
    verbose: bool = False,
    incremental: bool = False,
    merge: bool = False,
    write_to_disk: bool = True,
    allow_pre_commands: bool = True,
) -> CollectResult:
    if output_dir is None:
        output_dir = config.output_dir

    project_name = config.project_name
    out_path = root / output_dir
    out_path.mkdir(parents=True, exist_ok=True)

    created_files, tokens_by_file, parts, metrics = _collect(
        profile,
        project_name,
        str(out_path),
        root=root,
        verbose=verbose,
        incremental=incremental,
        merge=merge,
        query=query,
        mode=mode,
        allow_pre_commands=allow_pre_commands,
    )

    if not write_to_disk:
        for fp in created_files:
            with contextlib.suppress(OSError):
                Path(fp).unlink()
        created_files = []

    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0

    return CollectResult(parts=parts, files=created_files, tokens=total_tokens, metrics=metrics)
