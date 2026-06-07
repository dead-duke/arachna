"""Language and engine presets for arachna init."""

import json
from pathlib import Path

_SEPARATOR = "-" * 50
DEFAULT_PRESETS_PATH = "presets.json"


def _detect_dir(path: str) -> bool:
    p = Path(path)
    return p.is_dir() and any(p.rglob("*.*"))


def _detect_file(path: str) -> bool:
    return Path(path).exists()


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


def _load_builtin_presets() -> dict[str, dict]:
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


def _is_safe_tokenizer(spec: str) -> bool:
    from .tokenizer import _is_safe_tokenizer as _tok_safe

    return _tok_safe(spec)


def load_presets_from_file(path: str | Path) -> dict[str, dict]:
    p = Path(path)
    if not p.exists():
        return {}

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: failed to load {path}: {e}")
        return {}

    if not isinstance(data, dict):
        print(f"Warning: {path} must contain a JSON object, got {type(data).__name__}")
        return {}

    result = {}
    for name, preset in data.items():
        if not isinstance(preset, dict):
            print(f"Warning: preset '{name}' is not an object, skipping")
            continue

        unknown_keys = set(preset.keys()) - _VALID_PRESET_KEYS
        if unknown_keys:
            print(f"Warning: preset '{name}' has unknown keys: {', '.join(sorted(unknown_keys))}")

        split_mode = preset.get("split_mode", "by_file")
        if split_mode not in _VALID_SPLIT_MODES:
            print(
                f"Warning: preset '{name}' has invalid split_mode '{split_mode}', "
                f"must be one of {', '.join(sorted(_VALID_SPLIT_MODES))}"
            )
            continue

        max_tokens = preset.get("max_tokens", 16000)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            print(f"Warning: preset '{name}' max_tokens must be > 0, got {max_tokens}")
            continue

        tokenizer = preset.get("tokenizer", "default")
        if not _is_safe_tokenizer(tokenizer):
            print(
                f"Warning: preset '{name}' has unsafe tokenizer '{tokenizer}', "
                f"using 'default' instead. Only 'default', 'tiktoken', 'transformers', "
                f"or local .py files with safe imports are allowed."
            )
            preset["tokenizer"] = "default"

        for list_field in ("dirs", "patterns", "files", "pre_commands", "detect"):
            if list_field in preset and not isinstance(preset[list_field], list):
                print(
                    f"Warning: preset '{name}' field '{list_field}' must be a list, "
                    f"got {type(preset[list_field]).__name__}"
                )
                preset[list_field] = []

        result[name] = preset

    return result


def get_all_presets(external_path: str | Path | None = None) -> dict[str, dict]:
    if external_path is None:
        external_path = DEFAULT_PRESETS_PATH
    merged = _load_builtin_presets()
    external = load_presets_from_file(external_path)
    merged.update(external)
    return merged


def fetch_presets(url: str) -> dict[str, dict]:
    import contextlib
    import urllib.request

    try:
        with contextlib.closing(urllib.request.urlopen(url, timeout=10)) as response:
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
        result[name] = preset

    return result


def merge_presets(builtin: dict, remote: dict, local: dict) -> dict:
    merged = dict(builtin)
    for name, preset in remote.items():
        if name not in local:
            merged[name] = preset
    merged.update(local)
    return merged


def detect_presets(
    preset_name: str | None = None,
    external_path: str | Path | None = None,
) -> list[str]:
    all_presets = get_all_presets(external_path)

    if preset_name:
        if preset_name not in all_presets:
            print(f"Warning: preset '{preset_name}' not found in built-in or external presets")
            return []

        preset = all_presets[preset_name]
        detect_paths = preset.get("detect", [])

        if not detect_paths:
            return [preset_name]

        if not _detect_any(detect_paths):
            print(
                f"Warning: preset '{preset_name}' doesn't match this project "
                f"(none of {detect_paths} found)"
            )
            return []

        return [preset_name]

    detected: list[str] = []
    for name, preset in all_presets.items():
        detect_paths = preset.get("detect", [])
        if not detect_paths:
            continue
        if _detect_any(detect_paths):
            detected.append(name)

    return detected


def _detect_any(paths: list[str]) -> bool:
    cwd = Path.cwd()
    for p in paths:
        if "*" in p or "?" in p:
            if list(cwd.glob(p)):
                return True
        elif _detect_dir(p) or _detect_file(p):
            return True
    return False


def preset_to_profile(name: str, external_path: str | Path | None = None) -> dict | None:
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
        profile["directories"] = [d for d in dirs if _detect_dir(d)]

    patterns = preset.get("patterns", [])
    if patterns:
        profile["patterns"] = patterns

    files = preset.get("files", [])
    if files:
        profile["files"] = [f for f in files if _detect_file(f)]

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


def get_detected_summary(external_path: str | Path | None = None) -> dict[str, dict]:
    all_presets = get_all_presets(external_path)
    detected_names = detect_presets(external_path=external_path)
    return {name: all_presets[name] for name in detected_names if name in all_presets}
