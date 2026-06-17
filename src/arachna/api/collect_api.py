# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Public Collection API for arachna v4.0.0."""

import contextlib
from pathlib import Path

from ..config.config import get_profile, load_config
from ..domain.api_types import CollectResult
from ..domain.collector import collect as _collect
from .api_errors import ProfileNotFoundError


def collect(
    root: Path,
    profile: str | dict = "full",
    output_dir: str | None = None,
    query: str | None = None,
    mode: str = "full",
    verbose: bool = False,
    incremental: bool = False,
    merge: bool = False,
    write_to_disk: bool = True,
    allow_pre_commands: bool = True,
) -> CollectResult:
    if isinstance(profile, str):
        config = load_config(root=root)
        try:
            profile_dict = get_profile(profile, root=root, config=config)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile

    if output_dir is None:
        config = load_config(root=root)
        output_dir = config.get("output_dir", "arachna_context")

    project_name = profile_dict.get("project_name", "Project")
    out_path = root / output_dir
    out_path.mkdir(parents=True, exist_ok=True)

    created_files, tokens_by_file, parts, metrics = _collect(
        profile_dict,
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
