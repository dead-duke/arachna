"""Plugin benchmarks for snapshot layer — structural-diff and tiktoken."""

import time
from pathlib import Path
from typing import Any

from ..config.profile_config import ProfileConfig
from ..config.profiler import make_profile
from ..domain.collection.collector import clean_manifest, collect
from ..domain.path_utils import SafePath


def benchmark_plugins(
    profile: ProfileConfig, output_dir: str, root: Path
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    try:
        import tree_sitter  # noqa: F401
        import tree_sitter_python  # noqa: F401

        results["structural-diff"] = benchmark_structural_diff(profile, output_dir, root)
    except ImportError:
        pass
    try:
        from ..domain.tokenization.tokenizer import _has_tiktoken

        if _has_tiktoken():
            results["tiktoken"] = benchmark_tiktoken(profile, output_dir, root)
    except ImportError:
        pass
    return results


def benchmark_structural_diff(
    profile: ProfileConfig, output_dir: str, root: Path
) -> dict[str, Any]:
    from .diff.snapshot_diff import compute_diff as snapshots_diff
    from .diff.snapshot_diff import create_snapshot

    out = SafePath(root / output_dir, root)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    sid = create_snapshot(profile, name="bench-struct", root=root)
    create_time = time.perf_counter() - t0
    t0 = time.perf_counter()
    diffs = snapshots_diff(sid, profile, root=root, fmt="markdown")
    diff_time = time.perf_counter() - t0
    from .diff.differ_structural import structural_diff_sections

    t0 = time.perf_counter()
    struct_diffs = structural_diff_sections(diffs, "markdown")
    struct_time = time.perf_counter() - t0
    from .store.store import delete_snapshot

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


def benchmark_tiktoken(profile: ProfileConfig, output_dir: str, root: Path) -> dict[str, Any]:
    out = SafePath(root / output_dir, root)
    out.mkdir(parents=True, exist_ok=True)
    default_p = make_profile(profile, name_template="bench-full")
    _, tokens_d, _parts_d, _metrics_d = collect(
        default_p,
        "Bench",
        str(out),
        root=root,
        mode="full",
        incremental=False,
    )
    default_tokens = sum(tokens_d.values()) if isinstance(tokens_d, dict) else 0
    clean_manifest(out, "bench-full")
    tik_p = make_profile(profile, tokenizer="tiktoken", name_template="bench-full")
    created, tokens_by_file, parts, _metrics = collect(
        tik_p,
        "Bench",
        str(out),
        root=root,
        mode="full",
        incremental=False,
    )
    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
    clean_manifest(out, "bench-full")
    return {
        "parts": len(parts),
        "tokens": total_tokens,
        "time": 0,
        "files": len(created),
        "detail": {
            "default_tokens": default_tokens,
            "tiktoken_tokens": total_tokens,
            "ratio": f"{total_tokens / max(1, default_tokens):.2f}x",
        },
    }
