# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Remote repository collection.

Clones a git repository via --depth 1, selects profile by explicit
name or remote:true marker, runs collection, and cleans up.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..api.collect_api import collect
from ..config.config import load_config
from ..config.presets import detect_presets


def collect_remote(
    url: str, profile: str = "full", output_dir: str | None = None, root: Path | None = None
) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Only http:// and https:// URLs are allowed. Got: {url}")
    if shutil.which("git") is None:
        raise RuntimeError(
            "git is not installed. Install git to use --repo:\n  macOS: brew install git\n  Ubuntu/Debian: sudo apt install git\n  Windows: https://git-scm.com/download/win"
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
        has_config = (repo_path / ".arachna.json").exists()
        profile_name = _select_profile(
            requested=profile, profiles=profiles, has_config=has_config, repo_path=repo_path
        )
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


def _select_strict(requested, has_config, profiles):
    if not has_config:
        raise ValueError(
            f"Profile '{requested}' not found. Remote repository has no .arachna.json. Omit --profile to auto-detect, or add .arachna.json with a '{requested}' profile."
        )
    if requested not in profiles:
        available = list(profiles.keys())
        raise ValueError(
            f"Profile '{requested}' not found in remote repository. Available profiles: {', '.join(sorted(available)) if available else 'none'}."
        )
    return requested


def _auto_select(has_config, profiles, repo_path):
    if has_config:
        remote_profiles = {name: prof for name, prof in profiles.items() if prof.get("remote")}
        if len(remote_profiles) == 1:
            return next(iter(remote_profiles))
        if len(remote_profiles) > 1:
            raise ValueError(
                f"Multiple profiles with remote:true found: {', '.join(sorted(remote_profiles))}. Use --profile to select one."
            )
    detected = detect_presets(root=repo_path)
    return detected[0] if detected else "full"


def _select_profile(requested: str, profiles: dict, has_config: bool, repo_path: Path) -> str:
    if requested != "full":
        return _select_strict(requested, has_config, profiles)
    return _auto_select(has_config, profiles, repo_path)
