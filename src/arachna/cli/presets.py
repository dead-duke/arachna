# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna presets' command."""

import json
import sys
from pathlib import Path

from ..config.presets import (
    _load_builtin_presets,
    load_presets_from_file,
)
from ..config.presets_remote import fetch_presets, merge_presets
from ..config.profile_config import ArachnaConfig
from ..domain.atomic_write import atomic_write_text
from ..domain.path_utils import SafePath
from . import register


@register("presets-update")
def _cmd_presets_update(args, config: ArachnaConfig | dict):
    url = args.url or "https://raw.githubusercontent.com/dead-duke/arachna/main/presets.json"
    if not url.startswith(("http://", "https://")):
        print("Error: only http:// and https:// URLs are allowed for security reasons.")
        print(f"  Got: {url}")
        sys.exit(1)

    root = Path(config._root or ".") if hasattr(config, "_root") else Path(config.get("_root", "."))
    presets_path = SafePath(root / "presets.json", root)

    local = load_presets_from_file(presets_path.to_path())
    if local:
        print(f"Local presets.json: {len(local)} preset(s) — will be preserved.")
    elif presets_path.exists():
        print("Warning: local presets.json exists but could not be loaded. Aborting.")
        print("  Fix or remove the file and try again.")
        sys.exit(1)

    print(f"Fetching presets from {url}...")
    remote = fetch_presets(url)
    if not remote:
        print("No presets fetched. Check URL or network.")
        sys.exit(1)

    builtin = _load_builtin_presets()
    merged = merge_presets(builtin, remote, local)

    out = json.dumps(merged, indent=2) + "\n"
    atomic_write_text(presets_path.to_path(), out)
    new_count = len(remote)
    local_count = len(local)
    print(
        f"Presets updated: {len(merged)} total ({new_count} remote, {local_count} local preserved)."
    )
    print("Saved to presets.json")
