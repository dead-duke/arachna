"""Language and engine presets for arachna init."""

import functools
import json
from pathlib import Path

from ...domain.path_utils import SafePath
from ...domain.tokenization.tokenizer import _is_safe_tokenizer as _tokenizer_is_safe
from .. import VALID_SPLIT_MODES

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
    "remote",
}


def _load_builtin_presets_raw() -> dict[str, dict]:
    presets_root = Path(__file__).parent.parent.parent
    presets_dir = SafePath(presets_root / "presets", presets_root)
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


@functools.lru_cache(maxsize=1)
def _load_builtin_presets_cached() -> dict[str, dict]:
    return _load_builtin_presets_raw()


def _load_builtin_presets() -> dict[str, dict]:
    return _load_builtin_presets_cached()


def _is_safe_tokenizer(spec: str) -> bool:
    return _tokenizer_is_safe(spec)


def _validate_preset_split_mode(preset, name):
    split_mode = preset.get("split_mode", "by_file")
    if split_mode not in VALID_SPLIT_MODES:
        print(
            f"Warning: preset '{name}' has invalid split_mode '{split_mode}', must be one of {', '.join(sorted(VALID_SPLIT_MODES))}"
        )
        return None
    return split_mode


def _validate_preset_max_tokens(preset, name):
    max_tokens = preset.get("max_tokens", 16000)
    if not isinstance(max_tokens, int) or max_tokens < -1 or max_tokens == 0:
        print(
            f"Warning: preset '{name}' max_tokens must be -1 (unlimited) or >= 1, got {max_tokens}"
        )
        return None
    return max_tokens


def _validate_preset_tokenizer(preset):
    tokenizer = preset.get("tokenizer", "default")
    if not _is_safe_tokenizer(tokenizer):
        print(f"Warning: preset has unsafe tokenizer '{tokenizer}', using 'default' instead.")
        preset = dict(preset)
        preset["tokenizer"] = "default"
    return preset


def _validate_preset_lists(preset):
    for list_field in ("dirs", "patterns", "files", "pre_commands", "detect"):
        if list_field in preset and not isinstance(preset[list_field], list):
            print(
                f"Warning: preset field '{list_field}' must be a list, got {type(preset[list_field]).__name__}"
            )
            preset = dict(preset)
            preset[list_field] = []
    return preset


def _validate_preset(name: str, preset: dict) -> dict | None:
    if not isinstance(preset, dict):
        print(f"Warning: preset '{name}' is not an object, skipping")
        return None
    unknown_keys = set(preset.keys()) - _VALID_PRESET_KEYS
    if unknown_keys:
        print(f"Warning: preset '{name}' has unknown keys: {', '.join(sorted(unknown_keys))}")
    if _validate_preset_split_mode(preset, name) is None:
        return None
    if _validate_preset_max_tokens(preset, name) is None:
        return None
    preset = _validate_preset_tokenizer(preset)
    return _validate_preset_lists(preset)


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
    merged.update(load_presets_from_file(external_path))
    return merged


def detect_presets(preset_name=None, external_path=None, root=None) -> list[str]:
    if root is None:
        root = Path.cwd()
    all_presets = get_all_presets(external_path)
    if preset_name:
        return _detect_by_name(preset_name, all_presets, root)
    return _detect_all(all_presets, root)


def _detect_by_name(preset_name, all_presets, root):
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


def _detect_all(all_presets, root):
    detected = []
    for name, preset in all_presets.items():
        if preset.get("detect") and _detect_any(preset["detect"], root=root):
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


def _add_profile_dirs(profile, preset, root):
    dirs = preset.get("dirs", [])
    if dirs:
        profile["directories"] = [d for d in dirs if _detect_dir(d, root=root)]


def _add_profile_files(profile, preset, root):
    files = preset.get("files", [])
    if files:
        profile["files"] = [f for f in files if _detect_file(f, root=root)]


def _add_profile_optional_fields(profile, preset):
    patterns = preset.get("patterns", [])
    if patterns:
        profile["patterns"] = patterns
    split_marker = preset.get("split_marker")
    if split_marker:
        profile["split_marker"] = split_marker
    pre_commands = preset.get("pre_commands", [])
    if pre_commands:
        profile["pre_commands"] = pre_commands
    if preset.get("remote", False):
        profile["remote"] = True


def _build_profile_base(preset, root):
    profile = {
        "split_mode": preset.get("split_mode", "by_file"),
        "max_tokens": preset.get("max_tokens", 16000),
    }
    tokenizer = preset.get("tokenizer", "default")
    if tokenizer != "default" and _is_safe_tokenizer(tokenizer):
        profile["tokenizer"] = tokenizer
    _add_profile_dirs(profile, preset, root)
    _add_profile_files(profile, preset, root)
    _add_profile_optional_fields(profile, preset)
    return profile


def preset_to_profile(name, external_path=None, root=None):
    if root is None:
        root = Path.cwd()
    all_presets = get_all_presets(external_path)
    preset = all_presets.get(name)
    if preset is None:
        return None
    profile = _build_profile_base(preset, root)
    pre_commands = preset.get("pre_commands", [])
    if name == "git" and pre_commands:
        for key in ("directories", "patterns", "files", "pre_commands"):
            profile.pop(key, None)
        profile["command"] = pre_commands[0]
    return profile


def get_detected_summary(external_path=None, root=None):
    if root is None:
        root = Path.cwd()
    all_presets = get_all_presets(external_path)
    detected_names = detect_presets(external_path=external_path, root=root)
    return {name: all_presets[name] for name in detected_names if name in all_presets}
