# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna presets' command."""

import json
import sys
from pathlib import Path

from ..presets import _load_builtin_presets, fetch_presets, load_presets_from_file, merge_presets
from . import register


@register("presets-update")
def _cmd_presets_update(args, config: dict):
    url = args.url or "https://raw.githubusercontent.com/dead-duke/arachna/main/presets.json"
    if not url.startswith(("http://", "https://")):
        print("Error: only http:// and https:// URLs are allowed for security reasons.")
        print(f"  Got: {url}")
        sys.exit(1)

    local = load_presets_from_file("presets.json")
    if local:
        print(f"Local presets.json: {len(local)} preset(s) — will be preserved.")
    elif Path("presets.json").exists():
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
    Path("presets.json").write_text(out)
    new_count = len(remote)
    local_count = len(local)
    print(
        f"Presets updated: {len(merged)} total ({new_count} remote, {local_count} local preserved)."
    )
    print("Saved to presets.json")
