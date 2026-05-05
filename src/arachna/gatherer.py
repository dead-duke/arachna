"""Content gatherer — collects files and runs commands."""

from pathlib import Path
from typing import Any

from .formatter import format_file_section, is_excluded
from .gitignore import load_gitignore_patterns
from .runner import run_command
from .splitter import split
from .tokenizer import count_tokens


def gather_files(profile: dict[str, Any], verbose: bool = False) -> list[str]:
    """Collect content from directories, files, and pre_commands."""
    sections = []
    exclude = list(profile.get("exclude_patterns", []))
    root = Path.cwd()

    # Add gitignore patterns
    if profile.get("use_gitignore", True):
        exclude.extend(load_gitignore_patterns(root))

    for cmd in profile.get("pre_commands", []):
        output = run_command(cmd)
        if output.strip():
            sections.append(output.strip())

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
                elif verbose:
                    print(f"  Skipped: {filepath}")

    for filepath_str in profile.get("files", []):
        filepath = Path(filepath_str)
        if not filepath.exists():
            if verbose:
                print(f"  Not found: {filepath}")
            continue
        if is_excluded(filepath, exclude):
            continue
        section = format_file_section(filepath)
        if section:
            sections.append(section)
        elif verbose:
            print(f"  Skipped: {filepath}")

    return sections


def gather_command(cmd: str) -> str:
    """Run a command and return its output."""
    return run_command(cmd)


def dry_run(profile: dict[str, Any]) -> dict:
    """Simulate collection with actual splitting."""
    exclude = list(profile.get("exclude_patterns", []))
    max_tokens = profile.get("max_tokens", 16000)
    name_tmpl = profile.get("name_template", "chat")
    split_mode = profile.get("split_mode", "by_file")
    split_marker = profile.get("split_marker", "\n\n")
    command = profile.get("command")
    root = Path.cwd()

    if profile.get("use_gitignore", True):
        exclude.extend(load_gitignore_patterns(root))

    named_sections = []
    if command:
        content = gather_command(command)
        tokens = count_tokens(content)
        named_sections.append(("command output", content, tokens))
    else:
        for cmd in profile.get("pre_commands", []):
            output = run_command(cmd)
            if output.strip():
                tokens = count_tokens(output)
                label = cmd if len(cmd) <= 50 else cmd[:47] + "..."
                named_sections.append((f"pre: {label}", output, tokens))
        for directory in profile.get("directories", []):
            for pattern in profile.get("patterns", ["*"]):
                for filepath in sorted(Path(directory).rglob(pattern)):
                    if not filepath.is_file():
                        continue
                    if is_excluded(filepath, exclude):
                        continue
                    section = format_file_section(filepath)
                    if section:
                        tokens = count_tokens(section)
                        named_sections.append((str(filepath), section, tokens))
        for filepath_str in profile.get("files", []):
            filepath = Path(filepath_str)
            if not filepath.exists():
                continue
            if is_excluded(filepath, exclude):
                continue
            section = format_file_section(filepath)
            if section:
                tokens = count_tokens(section)
                named_sections.append((str(filepath), section, tokens))

    raw_content = "\n\n".join(content for _, content, _ in named_sections)
    part_contents = split(raw_content, max_tokens, split_mode, split_marker)

    parts = []
    for i, content in enumerate(part_contents, 1):
        part_sections = []
        for name, sec_content, tokens in named_sections:
            if sec_content.strip() in content:
                part_sections.append((name, tokens))
        total_tokens = count_tokens(content)
        parts.append(
            {
                "part_num": i,
                "sections": part_sections,
                "total_tokens": total_tokens,
            }
        )

    return {
        "name_tmpl": name_tmpl,
        "max_tokens": max_tokens,
        "parts": parts,
    }
