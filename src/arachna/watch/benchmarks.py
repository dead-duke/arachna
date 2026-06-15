# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Plugin benchmarks for Watch — structural-diff and tiktoken.

These benchmarks depend on watch/ internals and live here,
not in config/profiler which knows only domain/.
"""

import time
from pathlib import Path
from typing import Any

from ..domain.collector import clean_manifest, collect


def benchmark_plugins(profile: dict, output_dir: str, root: Path) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    try:
        import tree_sitter  # noqa: F401
        import tree_sitter_python  # noqa: F401

        results["structural-diff"] = benchmark_structural_diff(profile, output_dir, root)
    except ImportError:
        pass
    try:
        from ..domain.tokenizer import _has_tiktoken

        if _has_tiktoken():
            results["tiktoken"] = benchmark_tiktoken(profile, output_dir, root)
    except ImportError:
        pass
    return results


def benchmark_structural_diff(profile: dict, output_dir: str, root: Path) -> dict[str, Any]:
    from .watcher import compute_diff as watcher_diff
    from .watcher import create_snapshot

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    sid = create_snapshot(profile, name="bench-struct", root=root)
    create_time = time.perf_counter() - t0
    t0 = time.perf_counter()
    diffs = watcher_diff(sid, profile, root=root, fmt="markdown")
    diff_time = time.perf_counter() - t0
    from .differ_structural import structural_diff_sections

    t0 = time.perf_counter()
    struct_diffs = structural_diff_sections(diffs, "markdown")
    struct_time = time.perf_counter() - t0
    from .store import delete_snapshot

    delete_snapshot(sid, root=root)
    return {
        "parts": len(struct_diffs),
        "tokens": sum(len(d.content) // 4 for d in struct_diffs),
        "time": create_time + diff_time + struct_time,
        "files": len(diffs),
        "detail": {
            "create": f"{create_time:.3f}s",
            "text_diff": f"{diff_time:.3f}s",
            "structural_diff": f"{struct_time:.3f}s",
        },
    }


def benchmark_tiktoken(profile: dict, output_dir: str, root: Path) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    default_result = _run_one(profile, output_dir, root, mode="full")
    p_tik = _make_profile(profile, tokenizer="tiktoken")
    t0 = time.perf_counter()
    created, tokens_by_file, parts, _metrics = collect(
        p_tik,
        "Bench",
        str(out),
        root=root,
        mode="full",
        incremental=False,
    )
    elapsed = time.perf_counter() - t0
    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
    clean_manifest(out, "bench-full")
    return {
        "parts": len(parts),
        "tokens": total_tokens,
        "time": elapsed,
        "files": len(created),
        "detail": {
            "default_tokens": default_result["tokens"],
            "tiktoken_tokens": total_tokens,
            "ratio": f"{total_tokens / max(1, default_result['tokens']):.2f}x",
        },
    }


def _make_profile(profile: dict, **overrides) -> dict:
    p = dict(profile)
    p.update(overrides)
    return p


def _run_one(profile, output_dir, root, mode="full", query=None, incremental=False):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    name_tmpl = f"bench-{mode}"
    p = _make_profile(profile, name_template=name_tmpl)
    t0 = time.perf_counter()
    created, tokens_by_file, parts, _metrics = collect(
        p,
        "Bench",
        str(out),
        root=root,
        mode=mode,
        query=query,
        incremental=incremental,
    )
    elapsed = time.perf_counter() - t0
    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
    clean_manifest(out, name_tmpl)
    return {"parts": len(parts), "tokens": total_tokens, "time": elapsed, "files": len(created)}
