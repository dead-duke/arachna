"""Remote presets fetching and merging."""

import contextlib
import json
import os as _os
import urllib.request


def _parse_fetched_presets(data, url):
    if not isinstance(data, dict):
        print(f"Warning: {url} must contain a JSON object, got {type(data).__name__}")
        return {}
    result = {}
    for name, preset in data.items():
        if not isinstance(preset, dict):
            continue
        if "detect" not in preset and "dirs" not in preset and "command" not in preset:
            continue
        from .presets import _validate_preset

        validated = _validate_preset(name, preset)
        if validated is not None:
            result[name] = validated
    return result


def fetch_presets(url: str, timeout: int | None = None) -> dict[str, dict]:
    if timeout is None:
        timeout = int(_os.environ.get("ARACHNA_PRESETS_TIMEOUT", "10"))
    if not url.startswith(("http://", "https://")):
        print(f"Warning: only http:// and https:// URLs are allowed. Got: {url}")
        return {}
    try:
        with contextlib.closing(
            urllib.request.urlopen(url, timeout=timeout)  # nosec B310
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: failed to fetch presets from {url}: {e}")
        return {}
    return _parse_fetched_presets(data, url)


def merge_presets(builtin: dict, remote: dict, local: dict) -> dict:
    from .presets import _validate_preset

    merged = dict(builtin)
    for name, preset in remote.items():
        if name not in local:
            validated = _validate_preset(name, preset)
            if validated is not None:
                merged[name] = validated
    merged.update(local)
    return merged
