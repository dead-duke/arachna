# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Language and engine presets for arachna init."""

import json
import os as _os
from pathlib import Path

_SEPARATOR = "-" * 50
DEFAULT_PRESETS_PATH = "presets.json"


def _detect_dir(path: str, root: Path | None = None) -> bool:
    if root is None:
        root = Path.cwd()
    p = root / path
    return p.is_dir() and any(p.rglob("*.*"))


def _detect_file(path: str, root: Path | None = None) -> bool:
    if root is None:
        root = Path.cwd()
    return (root / path).exists()


_VALID_PRESET_KEYS = {
    "dirs",
    "patterns",
    "files",
    "pre_commands",
    "max_tokens",
    "split_mode",
    "split_marker",
    "detect",
    "tokenizer",
}
_VALID_SPLIT_MODES = {"by_file", "by_paragraph", "by_marker", "single"}


def _load_builtin_presets_raw() -> dict[str, dict]:
    presets_dir = Path(__file__).parent / "presets"
    if not presets_dir.is_dir():
        return {}
    result = {}
    for preset_file in sorted(presets_dir.glob("*.json")):
        name = preset_file.stem
        try:
            data = json.loads(preset_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict):
            result[name] = data
    return result


_builtin_cache: tuple[float, dict[str, dict]] | None = None


def _load_builtin_presets() -> dict[str, dict]:
    global _builtin_cache
    presets_dir = Path(__file__).parent / "presets"
    if presets_dir.is_dir():
        try:
            dir_mtime = presets_dir.stat().st_mtime
        except OSError:
            dir_mtime = 0
    else:
        dir_mtime = 0
    if _builtin_cache is not None:
        cached_mtime, cached_data = _builtin_cache
        if cached_mtime == dir_mtime:
            return cached_data
    data = _load_builtin_presets_raw()
    _builtin_cache = (dir_mtime, data)
    return data


def _is_safe_tokenizer(spec: str) -> bool:
    from .tokenizer import _is_safe_tokenizer as _tok_safe

    return _tok_safe(spec)


def _validate_preset(name: str, preset: dict) -> dict | None:
    """Validate a single preset. Returns cleaned preset or None if invalid."""
    if not isinstance(preset, dict):
        print(f"Warning: preset '{name}' is not an object, skipping")
        return None
    unknown_keys = set(preset.keys()) - _VALID_PRESET_KEYS
    if unknown_keys:
        print(f"Warning: preset '{name}' has unknown keys: {', '.join(sorted(unknown_keys))}")
    split_mode = preset.get("split_mode", "by_file")
    if split_mode not in _VALID_SPLIT_MODES:
        print(
            f"Warning: preset '{name}' has invalid split_mode '{split_mode}', must be one of {', '.join(sorted(_VALID_SPLIT_MODES))}"
        )
        return None
    max_tokens = preset.get("max_tokens", 16000)
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        print(f"Warning: preset '{name}' max_tokens must be > 0, got {max_tokens}")
        return None
    tokenizer = preset.get("tokenizer", "default")
    if not _is_safe_tokenizer(tokenizer):
        print(
            f"Warning: preset '{name}' has unsafe tokenizer '{tokenizer}', using 'default' instead."
        )
        preset = dict(preset)
        preset["tokenizer"] = "default"
    for list_field in ("dirs", "patterns", "files", "pre_commands", "detect"):
        if list_field in preset and not isinstance(preset[list_field], list):
            print(
                f"Warning: preset '{name}' field '{list_field}' must be a list, got {type(preset[list_field]).__name__}"
            )
            preset = dict(preset)
            preset[list_field] = []
    return preset


def load_presets_from_file(path: str | Path) -> dict[str, dict]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        raw = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: failed to read {path}: {e}")
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Warning: failed to load {path}: {e}")
        return {}
    if not isinstance(data, dict):
        print(f"Warning: {path} must contain a JSON object, got {type(data).__name__}")
        return {}
    result = {}
    for name, preset in data.items():
        validated = _validate_preset(name, preset)
        if validated is not None:
            result[name] = validated
    return result


def get_all_presets(external_path: str | Path | None = None) -> dict[str, dict]:
    if external_path is None:
        external_path = DEFAULT_PRESETS_PATH
    merged = dict(_load_builtin_presets())
    external = load_presets_from_file(external_path)
    merged.update(external)
    return merged


def fetch_presets(url: str, timeout: int | None = None) -> dict[str, dict]:
    import contextlib
    import urllib.request

    if timeout is None:
        timeout = int(_os.environ.get("ARACHNA_PRESETS_TIMEOUT", "10"))

    try:
        with contextlib.closing(urllib.request.urlopen(url, timeout=timeout)) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: failed to fetch presets from {url}: {e}")
        return {}
    if not isinstance(data, dict):
        print(f"Warning: {url} must contain a JSON object, got {type(data).__name__}")
        return {}
    result = {}
    for name, preset in data.items():
        if not isinstance(preset, dict):
            continue
        if "detect" not in preset and "dirs" not in preset and "command" not in preset:
            continue
        validated = _validate_preset(name, preset)
        if validated is not None:
            result[name] = validated
    return result


def merge_presets(builtin: dict, remote: dict, local: dict) -> dict:
    merged = dict(builtin)
    for name, preset in remote.items():
        if name not in local:
            validated = _validate_preset(name, preset)
            if validated is not None:
                merged[name] = validated
    merged.update(local)
    return merged


def detect_presets(
    preset_name: str | None = None,
    external_path: str | Path | None = None,
    root: Path | None = None,
) -> list[str]:
    if root is None:
        root = Path.cwd()
    all_presets = get_all_presets(external_path)
    if preset_name:
        if preset_name not in all_presets:
            print(f"Warning: preset '{preset_name}' not found in built-in or external presets")
            return []
        preset = all_presets[preset_name]
        detect_paths = preset.get("detect", [])
        if not detect_paths:
            return [preset_name]
        if not _detect_any(detect_paths, root=root):
            print(
                f"Warning: preset '{preset_name}' doesn't match this project (none of {detect_paths} found)"
            )
            return []
        return [preset_name]
    detected: list[str] = []
    for name, preset in all_presets.items():
        detect_paths = preset.get("detect", [])
        if not detect_paths:
            continue
        if _detect_any(detect_paths, root=root):
            detected.append(name)
    return detected


def _detect_any(paths: list[str], root: Path | None = None) -> bool:
    if root is None:
        root = Path.cwd()
    for p in paths:
        if "*" in p or "?" in p:
            if list(root.glob(p)):
                return True
        elif _detect_dir(p, root=root) or _detect_file(p, root=root):
            return True
    return False


def preset_to_profile(
    name: str,
    external_path: str | Path | None = None,
    root: Path | None = None,
) -> dict | None:
    if root is None:
        root = Path.cwd()
    all_presets = get_all_presets(external_path)
    preset = all_presets.get(name)
    if preset is None:
        return None
    profile: dict = {
        "split_mode": preset.get("split_mode", "by_file"),
        "max_tokens": preset.get("max_tokens", 16000),
    }
    tokenizer = preset.get("tokenizer", "default")
    if tokenizer != "default" and _is_safe_tokenizer(tokenizer):
        profile["tokenizer"] = tokenizer
    dirs = preset.get("dirs", [])
    if dirs:
        profile["directories"] = [d for d in dirs if _detect_dir(d, root=root)]
    patterns = preset.get("patterns", [])
    if patterns:
        profile["patterns"] = patterns
    files = preset.get("files", [])
    if files:
        profile["files"] = [f for f in files if _detect_file(f, root=root)]
    split_marker = preset.get("split_marker")
    if split_marker:
        profile["split_marker"] = split_marker
    pre_commands = preset.get("pre_commands", [])
    if pre_commands:
        profile["pre_commands"] = pre_commands
    if name == "git" and pre_commands:
        git_cmd = pre_commands[0]
        profile.pop("directories", None)
        profile.pop("patterns", None)
        profile.pop("files", None)
        profile.pop("pre_commands", None)
        profile["command"] = git_cmd
    return profile


def get_detected_summary(
    external_path: str | Path | None = None,
    root: Path | None = None,
) -> dict[str, dict]:
    if root is None:
        root = Path.cwd()
    all_presets = get_all_presets(external_path)
    detected_names = detect_presets(external_path=external_path, root=root)
    return {name: all_presets[name] for name in detected_names if name in all_presets}
