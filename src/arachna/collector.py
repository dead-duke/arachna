"""Orchestrator — gathers content, splits by tokens, writes output files."""

import json
import time
from pathlib import Path
from typing import Any

from .cache import load_cache, save_cache
from .compressor import compress, estimate_savings
from .gatherer import _collect_named_sections, _get_exclude_patterns, gather_command
from .runner import run_command
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


def clean_manifest(out_dir: Path, name_tmpl: str = ""):
    prev = load_manifest(out_dir)
    for f in prev:
        if not name_tmpl or f.startswith(name_tmpl):
            p = out_dir / f
            if p.exists():
                p.unlink()
    if name_tmpl:
        for old in sorted(out_dir.glob(f"{name_tmpl}_*.md")):
            old.unlink()
        plain = out_dir / f"{name_tmpl}.md"
        if plain.exists():
            plain.unlink()


def collect(
    profile: dict[str, Any],
    project_name: str,
    output_dir: str,
    verbose: bool = False,
    incremental: bool = False,
) -> list[str]:
    name_tmpl = profile["name_template"]
    title_tmpl = profile["title_template"]
    max_tokens = profile["max_tokens"]
    split_mode = profile.get("split_mode", "by_file")
    split_marker = profile.get("split_marker", "\n\n")
    command = profile.get("command")
    do_compress = profile.get("compress", False)
    do_compress_indent = profile.get("compress_indent", False)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if command:
        raw_content = gather_command(command)
    else:
        exclude = _get_exclude_patterns(profile)
        if incremental:
            cache = load_cache(out_path)
            named_sections, new_cache = _collect_named_sections(
                profile, exclude, incremental=True, cache=cache
            )
            save_cache(out_path, new_cache)
        else:
            named_sections, _ = _collect_named_sections(profile, exclude)
        [name for name, _, _ in named_sections if not name.startswith("pre:")]
        raw_content = "\n\n".join(content for _, content, _ in named_sections)

    if do_compress and raw_content.strip():
        compressed = compress(raw_content, indent=do_compress_indent)
        if verbose:
            orig, comp, pct = estimate_savings(raw_content, compressed)
            print(f"  Compressed: ~{orig} -> ~{comp} tokens (-{pct:.0f}%)")
        raw_content = compressed

    if not raw_content.strip():
        return []

    parts = split(raw_content, max_tokens, split_mode, split_marker)
    total_parts = len(parts)

    created = []
    for i, part_content in enumerate(parts, 1):
        title = title_tmpl.format(project_name=project_name, part=i)
        filename = f"{name_tmpl}.md" if total_parts == 1 else f"{name_tmpl}_{i}.md"
        filepath = out_path / filename

        # Build table of contents for this part
        toc = _build_toc(part_content, i, total_parts, name_tmpl)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title)
            f.write(toc)
            f.write(part_content)

        created.append(str(filepath))

    # Run post_commands after writing files
    for cmd in profile.get("post_commands", []):
        output = run_command(cmd)
        if verbose and output.strip():
            print(f"  post: {output.strip()}")

    return created


def _build_toc(content: str, part_num: int, total_parts: int, name_tmpl: str) -> str:
    """Build table of contents listing files in this part."""
    lines = []
    files = []
    for line in content.split("\n"):
        if line.startswith("### "):
            fname = line[4:].strip()
            files.append(fname)

    if not files:
        return ""

    lines.append(f"\nPart {part_num} of {total_parts}. Files in this part:\n")
    for f in files:
        lines.append(f"  {f}")
    lines.append("")
    return "\n".join(lines) + "\n"
