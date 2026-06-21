"""Orchestrator - gathers content, splits by tokens, writes output files."""

import contextlib
import functools
import json
import logging
import os
import re
import time
from pathlib import Path

from ..config.profile_config import ProfileConfig
from .api_types import PipelineMetrics
from .atomic_write import atomic_write_text
from .cache import load_cache, save_cache
from .differ_stats import compute_diff_stats
from .gatherer import _assemble_content
from .gatherer_files import _get_exclude_patterns
from .path_utils import SafePath
from .runner import run_command
from .splitter import split_sections
from .tokenizer import load_tokenizer

logger = logging.getLogger("arachna.collector")

_MANIFEST = ".arachna_manifest.json"
_MERGE_LOCK_FILE = ".arachna_merge.lock"
_METRICS_FILE = ".arachna_metrics.json"


@functools.lru_cache(maxsize=1)
def _get_lock_functions():
    """Detect platform file locking and return (lock_fn, unlock_fn)."""
    try:
        import fcntl

        def lock_fn(f):
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)

        def unlock_fn(f):
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        return lock_fn, unlock_fn
    except ImportError:
        pass

    try:
        import msvcrt

        def lock_fn(f):
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

        def unlock_fn(f):
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

        return lock_fn, unlock_fn
    except ImportError:
        pass

    def lock_fn(f):
        lock_path = Path(str(f.name) + ".lock")
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.close(fd)
        f._arachna_lock_path = str(lock_path)

    def unlock_fn(f):
        if hasattr(f, "_arachna_lock_path"):
            with contextlib.suppress(OSError):
                Path(f._arachna_lock_path).unlink()

    logger.warning(
        "Neither fcntl nor msvcrt available - using O_CREAT|O_EXCL file lock. Merge mode may have reduced concurrency."
    )
    return lock_fn, unlock_fn


@contextlib.contextmanager
def _merge_lock(out_dir: SafePath):
    lock_path = out_dir / _MERGE_LOCK_FILE
    out_dir.mkdir(parents=True, exist_ok=True)
    lock_fn, _ = _get_lock_functions()
    try:
        with open(str(lock_path), "w") as lock_file:
            lock_fn(lock_file)
            yield
    finally:
        with contextlib.suppress(OSError):
            lock_path.unlink()


def load_manifest(out_dir: SafePath) -> list[str]:
    mf = out_dir / _MANIFEST
    if mf.exists():
        try:
            return json.loads(mf.read_text()).get("files", [])
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_manifest(out_dir: SafePath, files: list[str]):
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / _MANIFEST
    atomic_write_text(
        manifest_path.to_path(), json.dumps({"files": files, "time": time.time()}, indent=2)
    )


def _clean_numbered_files(out_dir: SafePath, name_tmpl: str):
    for old in sorted(out_dir.glob(f"{name_tmpl}_*.md")):
        old.unlink()
    plain = out_dir / f"{name_tmpl}.md"
    if plain.exists():
        plain.unlink()


def clean_manifest(out_dir: SafePath, name_tmpl: str = ""):
    prev = load_manifest(out_dir)
    for f in prev:
        if not name_tmpl or f.startswith(name_tmpl):
            p = out_dir / f
            if p.exists():
                p.unlink()
    if name_tmpl:
        _clean_numbered_files(out_dir, name_tmpl)


def _find_next_part_num(out_dir: SafePath, name_tmpl: str) -> int:
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


def _format_toc_entry(name, all_indices, idx):
    if name.startswith("pre: "):
        entry = name
    else:
        entry = Path(name).name if "/" in name or "\\" in name else name
    if all_indices is not None:
        split_count = sum(1 for indices in all_indices if idx in indices)
        if split_count > 1:
            entry += f" [split across {split_count} parts]"
    return entry


def _build_toc(named_sections, part_section_indices, part_num, total_parts, all_indices=None):
    unique_indices = list(dict.fromkeys(part_section_indices))
    files = []
    for idx in unique_indices:
        if idx < len(named_sections):
            files.append(_format_toc_entry(named_sections[idx][0], all_indices, idx))
    if not files:
        return ""
    lines = [f"\nPart {part_num} of {total_parts}. Files in this part:\n"]
    for f in files:
        lines.append(f"  {f}")
    lines.append("")
    return "\n".join(lines) + "\n"


def _write_parts(
    parts,
    section_indices,
    named_sections,
    out_path,
    name_tmpl,
    title_tmpl,
    project_name,
    tokenizer,
    merge=False,
):
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
            named_sections, indices, i, start_num + total_parts - 1, all_indices=section_indices
        )
        atomic_write_text(filepath.to_path(), title + toc + part_content)
        created.append(str(filepath))
        tokens_by_file[str(filepath)] = tokenizer(title + toc + part_content)
    return created, tokens_by_file


def _diff_part_header(stats: dict, part_num: int, total_parts: int) -> str:
    parts = []
    for key, label in [
        ("renamed", "renamed"),
        ("moved", "moved"),
        ("modified", "modified"),
        ("added", "added"),
        ("deleted", "deleted"),
    ]:
        if stats[key]:
            parts.append(f"{stats[key]} {label}")
    summary = ", ".join(parts) if parts else "no changes"
    return f"Part {part_num} of {total_parts}. Changes: {summary}\n\n"


def _build_part_stats(diff_sections, section_indices):
    part_stats = []
    for indices in section_indices:
        part_sections = [diff_sections[i] for i in indices if i < len(diff_sections)]
        part_stats.append(compute_diff_stats(part_sections))
    return part_stats


def _write_diff_parts(
    diff_sections, out_path, name_tmpl, title_tmpl, project_name, max_tokens, tokenizer
):
    contents = [s.content for s in diff_sections if s.content.strip()]
    if not contents:
        return []
    parts, section_indices = split_sections(
        contents, max_tokens, separator="\n\n", tokenizer=tokenizer
    )
    if not parts:
        return []
    named_sections = [(s.path, s.content, tokenizer(s.content)) for s in diff_sections]
    part_stats = _build_part_stats(diff_sections, section_indices)
    created = []
    total_parts = len(parts)
    for i, part_content in enumerate(parts, 1):
        title = title_tmpl.format(project_name=project_name, part=i, total=total_parts)
        filename = f"{name_tmpl}_{i}.md"
        filepath = out_path / filename
        indices = section_indices[i - 1] if (i - 1) < len(section_indices) else []
        toc = _build_toc(named_sections, indices, i, total_parts, all_indices=section_indices)
        header = _diff_part_header(part_stats[i - 1], i, total_parts)
        atomic_write_text(filepath.to_path(), title + header + toc + part_content)
        created.append(str(filepath))
    return created


def _run_post_commands(commands: list[str], root: Path, verbose: bool = False):
    for cmd in commands:
        output = run_command(cmd, root=root, allow_file_args=True)
        if verbose and output.strip():
            print(f"  post: {output.strip()}")


def _write_metrics(out_path: SafePath, metrics: PipelineMetrics):
    out_path.mkdir(parents=True, exist_ok=True)
    metrics_path = out_path / _METRICS_FILE
    payload = {
        "extract_time_ms": metrics.extract_time_ms,
        "transform_time_ms": metrics.transform_time_ms,
        "load_time_ms": metrics.load_time_ms,
        "files_read": metrics.files_read,
        "files_skipped": metrics.files_skipped,
        "tokens_raw": metrics.tokens_raw,
        "tokens_compressed": metrics.tokens_compressed,
        "compression_ratio": metrics.compression_ratio,
    }
    atomic_write_text(metrics_path.to_path(), json.dumps(payload, indent=2))


def _build_profile_for_collect(profile, name_template, allow_pre_commands):
    profile_dict = profile.to_dict() if isinstance(profile, ProfileConfig) else dict(profile)
    if not allow_pre_commands:
        profile_dict["pre_commands"] = []
        profile_dict["post_commands"] = []
    name_tmpl = name_template if name_template is not None else profile_dict["name_template"]
    return profile_dict, name_tmpl, profile_dict["title_template"]


def _build_tokenizer(profile, root):
    if isinstance(profile, ProfileConfig):
        spec = profile.tokenizer
        chars = profile.chars_per_token
    else:
        spec = profile.get("tokenizer", "default")
        chars = profile.get("chars_per_token")
    return load_tokenizer(spec, chars_per_token=chars, root=root)


def _build_metrics(extract_time_ms, named_sections, tokens_by_file):
    tokens_raw = sum(tokens for _name, _content, tokens in named_sections)
    file_sections = [s for s in named_sections if not s[0].startswith("pre: ")]
    tokens_compressed_val = sum(tokens_by_file.values()) if tokens_by_file else 0
    compression_ratio_val = tokens_compressed_val / tokens_raw if tokens_raw > 0 else 1.0
    return PipelineMetrics(
        extract_time_ms=extract_time_ms,
        transform_time_ms=0.0,
        load_time_ms=0.0,
        files_read=len(file_sections),
        files_skipped=0,
        tokens_raw=tokens_raw,
        tokens_compressed=tokens_compressed_val,
        compression_ratio=round(compression_ratio_val, 4),
    )


def collect(
    profile,
    project_name,
    output_dir,
    root,
    verbose=False,
    incremental=False,
    merge=False,
    query=None,
    mode="full",
    name_template=None,
    allow_pre_commands=True,
):
    profile_dict, name_tmpl, title_tmpl = _build_profile_for_collect(
        profile, name_template, allow_pre_commands
    )
    out_path = SafePath(root / output_dir, root)
    out_path.mkdir(parents=True, exist_ok=True)
    tokenizer = _build_tokenizer(profile, root)
    t0 = time.perf_counter()
    exclude = _get_exclude_patterns(profile, root=root)
    cache = load_cache(out_path) if incremental else None
    named_sections, parts, section_indices, new_cache = _assemble_content(
        profile,
        exclude,
        tokenizer,
        root,
        incremental=incremental,
        cache=cache,
        verbose=verbose,
        query=query,
        mode=mode,
    )
    if incremental:
        save_cache(out_path, new_cache)
    extract_time_ms = (time.perf_counter() - t0) * 1000
    if not parts:
        metrics = _build_metrics(extract_time_ms, [], {})
        _write_metrics(out_path, metrics)
        return [], [], [], metrics
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
    _run_post_commands(profile_dict.get("post_commands", []), root=root, verbose=verbose)
    metrics = _build_metrics(extract_time_ms, named_sections, tokens_by_file)
    _write_metrics(out_path, metrics)
    return created, tokens_by_file, parts, metrics
