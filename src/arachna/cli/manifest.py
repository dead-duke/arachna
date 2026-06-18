# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna manifest' command."""

import json
from pathlib import Path

from ..domain.collector import load_manifest
from ..domain.path_utils import SafePath
from ..domain.tokenizer import count_tokens
from . import register
from ._helpers import get_root, parse_output_dir


def _manifest_json(manifest_files, out_path, profiles, project_name):
    """Build and print JSON manifest output."""
    parts = []
    for f in manifest_files:
        fp = out_path / f
        if fp.exists():
            content = fp.read_text(encoding="utf-8")
            tokens = count_tokens(content)
            parts.append({"file": f, "tokens": tokens, "hash": None, "dependencies": []})
    output = {
        "project_name": project_name,
        "profiles": list(profiles.keys()) if profiles else ["default"],
        "parts": parts,
    }
    print(json.dumps(output, indent=2))


def _manifest_text(manifest_files, out_path, project_name):
    """Build and print text manifest output."""
    if not manifest_files:
        print("No collected files found.")
        return
    lines = [
        f"# {project_name} — MANIFEST\n",
        "\nAll collected files:\n",
    ]
    for f in sorted(manifest_files):
        fp = out_path / f
        if fp.exists():
            content = fp.read_text(encoding="utf-8")
            tokens = count_tokens(content)
            lines.append(f"  {f} (~{tokens} tokens)")
    lines.append(f"\nTotal: {len(manifest_files)} file(s)\n")
    print("\n".join(lines))


@register("manifest")
def _cmd_manifest(args, config: dict):
    root = get_root(config)
    output_dir = parse_output_dir(args, config)
    out_path = SafePath(root / output_dir, root) if root else SafePath(Path(output_dir))
    project_name = config.get("project_name", "Project")

    manifest_files = load_manifest(out_path)
    profiles = config.get("profiles", {})

    if args.json:
        _manifest_json(manifest_files, out_path, profiles, project_name)
    else:
        _manifest_text(manifest_files, out_path, project_name)
