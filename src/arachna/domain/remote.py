# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Remote repository collection for arachna v4.1.0.

Clones a git repository via --depth 1, auto-detects presets,
runs collection, and cleans up the temp directory.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..api.collect_api import collect
from ..config.config import load_config
from ..config.presets import detect_presets


def collect_remote(
    url: str,
    profile: str = "full",
    output_dir: str | None = None,
    root: Path | None = None,
) -> str:
    """Clone a remote git repository and collect its context.

    Args:
        url: Git repository URL (http:// or https:// only).
        profile: Profile name to use. Falls back to auto-detection
                 if not found in the cloned repo's config.
        output_dir: Directory for collected files (default: arachna_context).
        root: Base directory for temp clone (default: cwd).

    Returns:
        Summary string with repo URL, profile used, file/part/token counts.

    Raises:
        ValueError: If URL scheme is not http:// or https://.
        RuntimeError: If git is not installed.
        subprocess.CalledProcessError: If git clone fails.
    """
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Only http:// and https:// URLs are allowed. Got: {url}")

    if shutil.which("git") is None:
        raise RuntimeError(
            "git is not installed. Install git to use --repo:\n"
            "  macOS: brew install git\n"
            "  Ubuntu/Debian: sudo apt install git\n"
            "  Windows: https://git-scm.com/download/win"
        )

    work_root = root or Path.cwd()
    tmpdir = tempfile.mkdtemp(prefix="arachna_remote_", dir=str(work_root))
    repo_path = Path(tmpdir) / "repo"

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(repo_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

        config = load_config(root=repo_path)
        profiles = config.get("profiles", {})

        if profile in profiles:
            profile_name = profile
        else:
            detected = detect_presets(root=repo_path)
            profile_name = detected[0] if detected else "full"

        result = collect(
            root=repo_path,
            profile=profile_name,
            output_dir=output_dir or "arachna_context",
            write_to_disk=True,
            allow_pre_commands=False,
        )

        lines = [
            f"Repository: {url}",
            f"Profile: {profile_name}",
            f"Files collected: {len(result.files)}",
            f"Parts: {len(result.parts)}",
            f"Tokens: {result.tokens}",
        ]
        if result.metrics:
            lines.append(
                f"Read: {result.metrics.files_read} files in {result.metrics.extract_time_ms:.0f}ms"
            )
        return "\n".join(lines)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
