"""Public Collection API for arachna v2.0.0.

Provides programmatic access to context collection.
"""

from pathlib import Path

from .api_errors import ProfileNotFoundError
from .api_types import CollectResult
from .collector import collect as _collect
from .config import get_profile


def collect(
    profile: str | dict = "full",
    output_dir: str | None = None,
    query: str | None = None,
    mode: str = "full",
    verbose: bool = False,
    incremental: bool = False,
    merge: bool = False,
) -> CollectResult:
    """Collect project context into token-limited parts.

    Args:
        profile: Profile name (str) or profile dict.
        output_dir: Directory for output files. If None, uses .arachna.json config.
        query: Optional query string to filter files.
        mode: Output mode — "full", "headers", "repo-map".
        verbose: Print skipped files.
        incremental: Only collect changed files.
        merge: Append to existing output.

    Returns:
        CollectResult with parts (content strings), files (created file paths),
        and total token count.

    Raises:
        ProfileNotFoundError: profile name not found.
    """
    if isinstance(profile, str):
        try:
            profile_dict = get_profile(profile)
        except KeyError:
            raise ProfileNotFoundError(f"Profile '{profile}' not found.") from None
    else:
        profile_dict = profile

    if output_dir is None:
        from .config import load_config

        config = load_config()
        output_dir = config.get("output_dir", "arachna_context")

    project_name = profile_dict.get("project_name", "Project")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    created_files, tokens_by_file = _collect(
        profile_dict,
        project_name,
        str(out_path),
        verbose=verbose,
        incremental=incremental,
        merge=merge,
        query=query,
        mode=mode,
    )

    # Read parts back for the result
    parts = []
    total_tokens = 0
    for fp in sorted(created_files):
        try:
            content = Path(fp).read_text(encoding="utf-8")
            parts.append(content)
            total_tokens += tokens_by_file.get(fp, 0)
        except OSError:
            pass

    return CollectResult(
        parts=parts,
        files=created_files,
        tokens=total_tokens,
    )
