"""Content gatherer — collects files and runs commands."""

from pathlib import Path
from typing import Any

from .formatter import format_file_section, is_excluded
from .runner import run_command


def gather_files(profile: dict[str, Any]) -> list[str]:
    """Collect content from directories, files, and pre_commands.

    Returns list of markdown-formatted section strings.
    """
    sections = []
    exclude = profile.get("exclude_patterns", [])

    # Run pre_commands in order
    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd)
        if output.strip():
            sections.append(output.strip())

    # Collect files from directories
    for directory in profile.get("directories", []):
        for pattern in profile.get("patterns", ["*"]):
            for filepath in sorted(Path(directory).rglob(pattern)):
                if not filepath.is_file():
                    continue
                if is_excluded(filepath, exclude):
                    continue
                section = format_file_section(filepath)
                if section:
                    sections.append(section)

    # Collect specific files
    for filepath_str in profile.get("files", []):
        filepath = Path(filepath_str)
        if not filepath.exists():
            continue
        if is_excluded(filepath, exclude):
            continue
        section = format_file_section(filepath)
        if section:
            sections.append(section)

    return sections


def gather_command(cmd: str) -> str:
    """Run a command and return its output."""
    return run_command(cmd)
