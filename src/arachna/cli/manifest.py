# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna manifest' command."""

import json
from pathlib import Path

from ..domain.collector import load_manifest
from ..domain.tokenizer import count_tokens
from . import register
from ._helpers import parse_output_dir


def _get_root(config: dict) -> Path | None:
    root_str = config.get("_root")
    return Path(root_str) if root_str else None


@register("manifest")
def _cmd_manifest(args, config: dict):
    root = _get_root(config)
    output_dir = parse_output_dir(args, config)
    out_path = root / output_dir if root else Path(output_dir)
    project_name = config.get("project_name", "Project")

    manifest_files = load_manifest(out_path)

    if args.json:
        profiles = config.get("profiles", {})
        parts = []
        for f in manifest_files:
            fp = out_path / f
            if fp.exists():
                content = fp.read_text(encoding="utf-8")
                tokens = count_tokens(content)
                parts.append(
                    {
                        "file": f,
                        "tokens": tokens,
                        "hash": None,
                        "dependencies": [],
                    }
                )
        output = {
            "project_name": project_name,
            "profiles": list(profiles.keys()) if profiles else ["default"],
            "parts": parts,
        }
        print(json.dumps(output, indent=2))
    else:
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
