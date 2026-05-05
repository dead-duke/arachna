"""Orchestrator — gathers content, splits by tokens, writes output files."""

from pathlib import Path
from typing import Any

from .gatherer import dry_run, gather_command, gather_files
from .splitter import split


def collect(
    profile: dict[str, Any],
    project_name: str,
    output_dir: str,
    dry_run_mode: bool = False,
    verbose: bool = False,
) -> list[str] | dict:
    """Execute one profile and return list of created file paths.

    If dry_run_mode=True, returns statistics dict instead of writing files.
    """
    name_tmpl = profile["name_template"]
    title_tmpl = profile["title_template"]
    max_tokens = profile["max_tokens"]
    split_mode = profile.get("split_mode", "by_file")
    split_marker = profile.get("split_marker", "\n\n")
    command = profile.get("command")
    out_path = Path(output_dir)

    if dry_run_mode:
        return dry_run(profile)

    # Clean old files
    for old in sorted(out_path.glob(f"{name_tmpl}_*.md")):
        old.unlink()

    # Gather content
    if command:
        raw_content = gather_command(command)
    else:
        sections = gather_files(profile, verbose=verbose)
        raw_content = "\n\n".join(sections)

    if not raw_content.strip():
        return []

    # Split into token-limited parts
    parts = split(raw_content, max_tokens, split_mode, split_marker)

    # Write output files
    created = []
    for i, part_content in enumerate(parts, 1):
        title = title_tmpl.format(project_name=project_name, part=i)
        filename = f"{name_tmpl}_{i}.md"
        filepath = out_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title)
            f.write(part_content)

        created.append(str(filepath))

    return created
