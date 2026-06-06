"""Public Collection API for arachna v2.0.0.

Provides programmatic access to context collection.
Returns structured CollectResult instead of printing to stdout.

Usage:
    from arachna.collect_api import collect

    result = collect.collect(profile="full", mode="repo-map")
    print(f"Collected {result.tokens} tokens in {len(result.parts)} parts")
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

    Gathers files matching the profile, splits them by token limit,
    and writes output files. Returns structured data with part
    contents, file paths, and token count.

    Supports three collection modes:
    - "full": Complete file contents (default).
    - "headers": File contents with dependency/export headers.
      Headers are auto-enabled when query is used.
    - "repo-map": Function/class signatures only, no bodies.
      Saves 50-70% tokens for project overview.

    Query filtering scores files by relevance:
    - +10 for query word in filename
    - +8 for query word in exports (function/class names)
    - +5 for query word in imports (dependencies)
    - +3 for query word in file content
    Files with score > 0 are included. Files that import matched
    files are also included (import chain, depth 2).

    Args:
        profile: Profile name from .arachna.json (e.g. "full", "code")
                 or a profile dict with directories/patterns/files.
                 Default: "full".
        output_dir: Directory for output files. If None, reads
                    output_dir from .arachna.json config.
        query: Optional query string to filter files by relevance.
               Example: "authentication" matches auth.py, login handlers.
               None or empty string returns all files.
        mode: Collection mode — "full", "headers", or "repo-map".
        verbose: If True, prints skipped files to stdout.
        incremental: If True, only collects files changed since last run.
                     Uses .arachna_cache.json for change detection.
        merge: If True, appends new output files instead of replacing
               existing ones. Files are numbered sequentially.

    Returns:
        CollectResult with:
        - parts: list of output file contents as strings
        - files: list of created file paths
        - tokens: total token count across all parts

    Raises:
        ProfileNotFoundError: Profile name not found in .arachna.json.

    Example:
        >>> # Full collection
        >>> result = collect.collect(profile="full")
        >>> print(f"{result.tokens} tokens in {len(result.parts)} parts")
        >>>
        >>> # Filtered by query
        >>> result = collect.collect(profile="full", query="tokenizer")
        >>>
        >>> # Repo-map mode for project overview
        >>> result = collect.collect(profile="full", mode="repo-map")
        >>>
        >>> # Incremental — only changed files
        >>> result = collect.collect(profile="full", incremental=True)
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
