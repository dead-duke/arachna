"""Orchestrator — gathers content, splits by tokens, writes output files."""

import contextlib
import json
import logging
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from .cache import load_cache, save_cache
from .differ import DiffSection, compute_diff_stats
from .gatherer import _assemble_content, _get_exclude_patterns
from .runner import run_command
from .splitter import split_sections
from .tokenizer import count_tokens, load_tokenizer

logger = logging.getLogger("arachna.collector")

_MANIFEST = ".arachna_manifest.json"
_MERGE_LOCK_FILE = ".arachna_merge.lock"

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

        def _lock_file(f):
            lock_path = Path(str(f.name) + ".lock")
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.close(fd)
                f._arachna_lock_path = str(lock_path)
            except OSError:
                raise

        def _unlock_file(f):
            if hasattr(f, "_arachna_lock_path"):
                with contextlib.suppress(OSError):
                    Path(f._arachna_lock_path).unlink()

        logger.warning(
            "Neither fcntl nor msvcrt available — using O_CREAT|O_EXCL file lock. "
            "Merge mode may have reduced concurrency."
        )


@contextlib.contextmanager
def _merge_lock(out_dir: Path):
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
    with _merge_lock(out_dir):
        max_num = 0
        pattern = re.compile(rf"^{re.escape(name_tmpl)}_(\d+)\.md$")
        for f in out_dir.glob(f"{name_tmpl}_*.md"):
            m = pattern.match(f.name)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
        if (out_dir / f"{name_tmpl}.md").exists() and max_num == 0:
            max_num = 1
        return max_num + 1


def _build_toc(
    named_sections: list[tuple[str, str, int]],
    part_section_indices: list[int],
    part_num: int,
    total_parts: int,
    all_indices: list[list[int]] | None = None,
) -> str:
    """Build table of contents for a part.

    Deduplicates indices within the part. If all_indices is provided,
    appends [split across N parts] for sections split across multiple parts.
    """
    # Deduplicate indices within this part
    unique_indices = list(dict.fromkeys(part_section_indices))
    files = []
    for idx in unique_indices:
        if idx < len(named_sections):
            name = named_sections[idx][0]
            if name.startswith("pre: "):
                entry = name
            else:
                entry = Path(name).name if "/" in name or "\\" in name else name

            # Check if this section is split across multiple parts
            if all_indices is not None:
                split_count = sum(1 for indices in all_indices if idx in indices)
                if split_count > 1:
                    entry += f" [split across {split_count} parts]"

            files.append(entry)
    if not files:
        return ""
    lines = [f"\nPart {part_num} of {total_parts}. Files in this part:\n"]
    for f in files:
        lines.append(f"  {f}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _write_parts(
    parts: list[str],
    section_indices: list[list[int]],
    named_sections: list[tuple[str, str, int]],
    out_path: Path,
    name_tmpl: str,
    title_tmpl: str,
    project_name: str,
    tokenizer: Any,
    merge: bool = False,
) -> tuple[list[str], dict[str, int]]:
    total_parts = len(parts)
    start_num = _find_next_part_num(out_path, name_tmpl) if merge else 1
    created = []
    tokens_by_file = {}
    for i, part_content in enumerate(parts, start_num):
        part_idx = i - start_num
        title = title_tmpl.format(project_name=project_name, part=i, total=total_parts)
        filename = f"{name_tmpl}_{i}.md"
        filepath = out_path / filename
        indices = section_indices[part_idx] if part_idx < len(section_indices) else []
        toc = _build_toc(
            named_sections,
            indices,
            i,
            start_num + total_parts - 1,
            all_indices=section_indices,
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title)
            f.write(toc)
            f.write(part_content)
        created.append(str(filepath))
        tokens_by_file[str(filepath)] = tokenizer(title + toc + part_content)
    return created, tokens_by_file


def _diff_part_header(stats: dict, part_num: int, total_parts: int) -> str:
    parts = []
    if stats["renamed"]:
        parts.append(f"{stats['renamed']} renamed")
    if stats["moved"]:
        parts.append(f"{stats['moved']} moved")
    if stats["modified"]:
        parts.append(f"{stats['modified']} modified")
    if stats["added"]:
        parts.append(f"{stats['added']} added")
    if stats["deleted"]:
        parts.append(f"{stats['deleted']} deleted")
    summary = ", ".join(parts) if parts else "no changes"
    return f"Part {part_num} of {total_parts}. Changes: {summary}\n\n"


def _write_diff_parts(
    diff_sections: list[DiffSection],
    out_path: Path,
    name_tmpl: str,
    title_tmpl: str,
    project_name: str,
    max_tokens: int,
    tokenizer: Any,
    snapshot_id: str | None = None,
    to_snapshot_id: str | None = None,
) -> list[str]:
    contents = [s.content for s in diff_sections if s.content.strip()]
    if not contents:
        return []
    parts, section_indices = split_sections(
        contents, max_tokens, separator="\n\n", tokenizer=tokenizer
    )
    if not parts:
        return []
    named_sections = [(s.path, s.content, tokenizer(s.content)) for s in diff_sections]
    part_stats = []
    for indices in section_indices:
        part_sections = [diff_sections[i] for i in indices if i < len(diff_sections)]
        part_stats.append(compute_diff_stats(part_sections))
    created = []
    total_parts = len(parts)
    for i, part_content in enumerate(parts, 1):
        title = title_tmpl.format(project_name=project_name, part=i, total=total_parts)
        filename = f"{name_tmpl}_{i}.md"
        filepath = out_path / filename
        indices = section_indices[i - 1] if (i - 1) < len(section_indices) else []
        toc = _build_toc(
            named_sections,
            indices,
            i,
            total_parts,
            all_indices=section_indices,
        )
        header = _diff_part_header(part_stats[i - 1], i, total_parts)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title)
            f.write(header)
            f.write(toc)
            f.write(part_content)
        created.append(str(filepath))
    return created


def _run_post_commands(commands: list[str], verbose: bool = False):
    for cmd in commands:
        output = run_command(cmd, allow_file_args=True)
        if verbose and output.strip():
            print(f"  post: {output.strip()}")


def collect(
    profile: dict[str, Any],
    project_name: str,
    output_dir: str,
    verbose: bool = False,
    incremental: bool = False,
    merge: bool = False,
    query: str | None = None,
    mode: str = "full",
    name_template: str | None = None,
) -> tuple[list[str], dict[str, int], list[str]]:
    name_tmpl = name_template if name_template is not None else profile["name_template"]
    title_tmpl = profile["title_template"]
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    chars_per_token = profile.get("chars_per_token")
    tokenizer_spec = profile.get("tokenizer", "default")
    tokenizer = (
        load_tokenizer(tokenizer_spec, chars_per_token=chars_per_token)
        if tokenizer_spec != "default"
        else (
            lambda t: (
                count_tokens(t, chars_per_token=chars_per_token)
                if chars_per_token
                else count_tokens(t)
            )
        )
    )
    exclude = _get_exclude_patterns(profile)
    cache = load_cache(out_path) if incremental else None
    named_sections, parts, section_indices, new_cache = _assemble_content(
        profile,
        exclude,
        tokenizer,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        query=query,
        mode=mode,
    )
    if incremental:
        save_cache(out_path, new_cache)
    if not parts:
        return [], [], []
    created, tokens_by_file = _write_parts(
        parts,
        section_indices,
        named_sections,
        out_path,
        name_tmpl,
        title_tmpl,
        project_name,
        tokenizer,
        merge=merge,
    )
    _run_post_commands(profile.get("post_commands", []), verbose=verbose)
    return created, tokens_by_file, parts
