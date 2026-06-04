"""Orchestrator — gathers content, splits by tokens, writes output files."""

import contextlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from .cache import load_cache, save_cache
from .differ import DiffSection
from .gatherer import (
    _assemble_content,
    _get_exclude_patterns,
)
from .runner import run_command
from .splitter import split_sections
from .tokenizer import count_tokens, load_tokenizer

_MANIFEST = ".arachna_manifest.json"
_MERGE_LOCK_FILE = ".arachna_merge.lock"

# File locking for merge mode: prevents race condition when two
# processes compute _find_next_part_num concurrently.
# Uses fcntl.flock on Unix, msvcrt.locking on Windows,
# falls back to threading.Lock (no cross-process safety, but
# prevents thread races in single-process usage).
try:
    import fcntl

    def _lock_file(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock_file(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

except ImportError:
    try:
        import msvcrt

        def _lock_file(f):
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

        def _unlock_file(f):
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

    except ImportError:
        import threading

        _fallback_lock = threading.Lock()

        def _lock_file(f):
            _fallback_lock.acquire()

        def _unlock_file(f):
            _fallback_lock.release()


@contextlib.contextmanager
def _merge_lock(out_dir: Path):
    """Acquire a file-based lock for merge mode operations.

    Prevents race condition when two processes compute
    _find_next_part_num concurrently.

    On Unix: fcntl.flock (advisory, cross-process).
    On Windows: msvcrt.locking.
    Fallback: threading.Lock (same process only).
    """
    lock_path = out_dir / _MERGE_LOCK_FILE
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        with open(lock_path, "w") as lock_file:
            _lock_file(lock_file)
            yield
    finally:
        with contextlib.suppress(OSError):
            lock_path.unlink()


def load_manifest(out_dir: Path) -> list[str]:
    mf = out_dir / _MANIFEST
    if mf.exists():
        try:
            return json.loads(mf.read_text()).get("files", [])
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_manifest(out_dir: Path, files: list[str]):
    """Atomically write manifest to disk."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / _MANIFEST
    fd, tmp_path = tempfile.mkstemp(dir=str(out_dir), prefix=".arachna_manifest_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"files": files, "time": time.time()}, f, indent=2)
        os.replace(tmp_path, manifest_path)
    except Exception:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


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


def _find_next_part_num(out_dir: Path, name_tmpl: str) -> int:
    """Find the next available part number for merged output.

    Scans existing files matching name_tmpl_*.md and returns max_num + 1.
    Returns 1 if no existing files found.

    Uses file-based lock to prevent race conditions when multiple
    processes run merge mode concurrently.
    """
    with _merge_lock(out_dir):
        max_num = 0
        pattern = re.compile(rf"^{re.escape(name_tmpl)}_(\d+)\.md$")
        for f in out_dir.glob(f"{name_tmpl}_*.md"):
            m = pattern.match(f.name)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
        # Also check for the single-file case (name_tmpl.md)
        if (out_dir / f"{name_tmpl}.md").exists() and max_num == 0:
            max_num = 1
        return max_num + 1


def _build_toc(
    named_sections: list[tuple[str, str, int]],
    part_content: str,
    part_num: int,
    total_parts: int,
) -> str:
    """Build table of contents for a part.

    Uses named_sections to list files present in this part's content.
    Works for all output formats — detects files by matching section
    content strings, not markdown headers.
    """
    files = []
    for name, content, _tokens in named_sections:
        if content.strip() in part_content:
            # Extract filename from the name (may be "pre: ..." or full path)
            if name.startswith("pre: "):
                files.append(name)
            else:
                files.append(Path(name).name if "/" in name or "\\" in name else name)

    if not files:
        return ""

    lines = [f"\nPart {part_num} of {total_parts}. Files in this part:\n"]
    for f in files:
        lines.append(f"  {f}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _write_parts(
    parts: list[str],
    named_sections: list[tuple[str, str, int]],
    out_path: Path,
    name_tmpl: str,
    title_tmpl: str,
    project_name: str,
    tokenizer: Any,
    merge: bool = False,
) -> tuple[list[str], dict[str, int]]:
    """Write token-limited parts to output files.

    Returns (created_files, tokens_by_file) tuple.
    """
    total_parts = len(parts)
    start_num = _find_next_part_num(out_path, name_tmpl) if merge else 1

    created = []
    tokens_by_file = {}
    for i, part_content in enumerate(parts, start_num):
        title = title_tmpl.format(project_name=project_name, part=i, total=total_parts)
        if total_parts == 1 and not merge:
            filename = f"{name_tmpl}.md"
        elif total_parts == 1 and merge:
            filename = f"{name_tmpl}_{i}.md"
        else:
            filename = f"{name_tmpl}_{i}.md"
        filepath = out_path / filename

        toc = _build_toc(named_sections, part_content, i, start_num + total_parts - 1)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title)
            f.write(toc)
            f.write(part_content)

        created.append(str(filepath))
        tokens_by_file[str(filepath)] = tokenizer(title + toc + part_content)

    return created, tokens_by_file


def _write_diff_parts(
    diff_sections: list[DiffSection],
    out_path: Path,
    name_tmpl: str,
    title_tmpl: str,
    project_name: str,
    max_tokens: int,
    tokenizer: Any,
) -> list[str]:
    """Write diff sections to chat-diff_N.md files with token-based splitting.

    Uses split_sections for dense packing of diff content into
    token-limited parts.

    Returns list of created file paths.
    """
    # Build content strings from DiffSections
    contents = [s.content for s in diff_sections if s.content.strip()]

    if not contents:
        return []

    # Split into token-limited parts
    parts = split_sections(contents, max_tokens, separator="\n\n", tokenizer=tokenizer)

    if not parts:
        return []

    # Build named sections for TOC (path -> content mapping)
    named_sections = [(s.path, s.content, tokenizer(s.content)) for s in diff_sections]

    created = []
    total_parts = len(parts)
    for i, part_content in enumerate(parts, 1):
        title = title_tmpl.format(project_name=project_name, part=i, total=total_parts)
        filename = f"{name_tmpl}.md" if total_parts == 1 else f"{name_tmpl}_{i}.md"
        filepath = out_path / filename

        toc = _build_toc(named_sections, part_content, i, total_parts)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title)
            f.write(toc)
            f.write(part_content)

        created.append(str(filepath))

    return created


def _run_post_commands(commands: list[str], verbose: bool = False):
    """Execute post-collection commands."""
    for cmd in commands:
        output = run_command(cmd)
        if verbose and output.strip():
            print(f"  post: {output.strip()}")


def collect(
    profile: dict[str, Any],
    project_name: str,
    output_dir: str,
    verbose: bool = False,
    incremental: bool = False,
    merge: bool = False,
) -> tuple[list[str], dict[str, int]]:
    """Collect content and write output files.

    Returns (created_files, tokens_by_file) tuple.
    tokens_by_file maps filename -> token count for manifest generation.
    """
    name_tmpl = profile["name_template"]
    title_tmpl = profile["title_template"]
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Load tokenizer if specified
    tokenizer_spec = profile.get("tokenizer", "default")
    tokenizer = load_tokenizer(tokenizer_spec) if tokenizer_spec != "default" else count_tokens

    exclude = _get_exclude_patterns(profile)
    cache = load_cache(out_path) if incremental else None

    named_sections, parts, new_cache = _assemble_content(
        profile,
        exclude,
        tokenizer,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
    )

    if incremental:
        save_cache(out_path, new_cache)

    if not parts:
        return [], {}

    created, tokens_by_file = _write_parts(
        parts, named_sections, out_path, name_tmpl, title_tmpl, project_name, tokenizer, merge=merge
    )

    _run_post_commands(profile.get("post_commands", []), verbose=verbose)

    return created, tokens_by_file
