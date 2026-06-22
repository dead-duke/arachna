"""Remote repository collection."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from ..domain.collection.collector import collect as _domain_collect
from .core.config import get_profile, load_config
from .presets.presets import detect_presets
from .profile_config import ProfileConfig
from .urls import validate_remote_url


def collect_remote(
    url: str, profile: str = "full", output_dir: str | None = None, root: Path | None = None
) -> str:
    validate_remote_url(url)
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
        profiles = config.profiles
        has_config = (repo_path / ".arachna.json").exists()
        profile_name = _select_profile(
            requested=profile, profiles=profiles, has_config=has_config, repo_path=repo_path
        )
        profile_cfg = _resolve_profile_dict(profile_name, config, repo_path)
        result = _domain_collect(
            profile_cfg.to_dict(),
            config.project_name,
            output_dir or config.output_dir,
            root=repo_path,
            verbose=False,
            incremental=False,
            merge=False,
            query=None,
            mode="full",
            allow_pre_commands=False,
        )
        created_files, tokens_by_file, parts, metrics = result
        total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
        lines = [
            f"Repository: {url}",
            f"Profile: {profile_name}",
            f"Files collected: {len(created_files)}",
            f"Parts: {len(parts)}",
            f"Tokens: {total_tokens}",
        ]
        if metrics:
            lines.append(f"Read: {metrics.files_read} files in {metrics.extract_time_ms:.0f}ms")
        return "\n".join(lines)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _resolve_profile_dict(profile_name, config, repo_path) -> ProfileConfig:
    return get_profile(profile_name, root=repo_path, config=config)


def _select_strict(requested, has_config, profiles):
    if not has_config:
        raise ValueError(
            f"Profile '{requested}' not found. Remote repository has no .arachna.json."
        )
    if requested not in profiles:
        available = list(profiles.keys())
        raise ValueError(
            f"Profile '{requested}' not found. Available: {', '.join(sorted(available)) if available else 'none'}."
        )
    return requested


def _auto_select(has_config, profiles, repo_path):
    if has_config:
        remote_profiles = {name: prof for name, prof in profiles.items() if prof.remote}
        if len(remote_profiles) == 1:
            return next(iter(remote_profiles))
        if len(remote_profiles) > 1:
            raise ValueError(
                f"Multiple profiles with remote:true: {', '.join(sorted(remote_profiles))}."
            )
    detected = detect_presets(root=repo_path)
    return detected[0] if detected else "full"


def _select_profile(requested, profiles, has_config, repo_path):
    if requested != "full":
        return _select_strict(requested, has_config, profiles)
    return _auto_select(has_config, profiles, repo_path)
