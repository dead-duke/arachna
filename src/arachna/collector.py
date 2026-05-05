"""Orchestrator — gathers content, splits by tokens, writes output files."""

import json
import time
from pathlib import Path
from typing import Any

from .gatherer import gather_command, gather_files
from .splitter import split

_MANIFEST = ".arachna_manifest.json"


def load_manifest(out_dir: Path) -> list[str]:
    mf = out_dir / _MANIFEST
    if mf.exists():
        try:
            return json.loads(mf.read_text()).get("files", [])
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_manifest(out_dir: Path, files: list[str]):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / _MANIFEST).write_text(json.dumps({"files": files, "time": time.time()}, indent=2))


def clean_manifest(out_dir: Path, current_name_tmpl: str):
    prev = load_manifest(out_dir)
    for f in prev:
        p = out_dir / f
        if p.exists():
            p.unlink()
    for old in sorted(out_dir.glob(f"{current_name_tmpl}_*.md")):
        old.unlink()
    plain = out_dir / f"{current_name_tmpl}.md"
    if plain.exists():
        plain.unlink()


def collect(
    profile: dict[str, Any],
    project_name: str,
    output_dir: str,
    verbose: bool = False,
) -> list[str]:
    name_tmpl = profile["name_template"]
    title_tmpl = profile["title_template"]
    max_tokens = profile["max_tokens"]
    split_mode = profile.get("split_mode", "by_file")
    split_marker = profile.get("split_marker", "\n\n")
    command = profile.get("command")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if command:
        raw_content = gather_command(command)
    else:
        sections = gather_files(profile, verbose=verbose)
        raw_content = "\n\n".join(sections)

    if not raw_content.strip():
        return []

    parts = split(raw_content, max_tokens, split_mode, split_marker)

    created = []
    for i, part_content in enumerate(parts, 1):
        title = title_tmpl.format(project_name=project_name, part=i)
        filename = f"{name_tmpl}.md" if len(parts) == 1 else f"{name_tmpl}_{i}.md"
        filepath = out_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title)
            f.write(part_content)

        created.append(str(filepath))

    return created
