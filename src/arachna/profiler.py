# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Benchmark module for arachna v3.2.

Measures real token savings and performance across all collection modes.
Runs on the user's actual project, not synthetic tests.
"""

import json
import time
from pathlib import Path
from typing import Any

from .collector import clean_manifest, collect


def _make_profile(profile: dict, **overrides) -> dict:
    """Return a copy of profile with overrides applied."""
    p = dict(profile)
    p.update(overrides)
    return p


def _run_one(
    profile: dict,
    output_dir: str,
    mode: str = "full",
    query: str | None = None,
    incremental: bool = False,
) -> dict[str, Any]:
    """Run one benchmark iteration. Returns {parts, tokens, time, files}."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    name_tmpl = f"bench-{mode}"
    p = _make_profile(profile, name_template=name_tmpl)
    t0 = time.perf_counter()
    created, tokens_by_file, parts = collect(
        p, "Bench", str(out), mode=mode, query=query, incremental=incremental
    )
    elapsed = time.perf_counter() - t0
    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
    clean_manifest(out, name_tmpl)
    return {
        "parts": len(parts),
        "tokens": total_tokens,
        "time": elapsed,
        "files": len(created),
    }


def run_benchmark(profile: dict, output_dir: str) -> dict[str, dict[str, Any]]:
    """Run all benchmark modes on the given profile.

    Order matters: full first (baseline), then incremental variants,
    then other modes. Incremental uses cache from full run.
    """
    results: dict[str, dict[str, Any]] = {}

    # 1. Full — baseline
    results["full"] = _run_one(profile, output_dir, mode="full")

    # 2. Full + compress
    p_compress = _make_profile(profile, compress=True)
    results["compress"] = _run_one(p_compress, output_dir, mode="full")

    # 3. Repo-map
    results["repo-map"] = _run_one(profile, output_dir, mode="repo-map")

    # 4. Headers
    results["headers"] = _run_one(profile, output_dir, mode="headers")

    # 5. Incremental — first run (warm cache)
    results["incremental"] = _run_one(profile, output_dir, mode="full", incremental=True)

    # 6. Query — use first file from profile as query
    query = _find_query_candidate(profile)
    if query:
        results["query"] = _run_one(profile, output_dir, mode="full", query=query)

    # 7. Plugin comparison — if plugins available
    plugin_results = _benchmark_plugins(profile, output_dir)
    if plugin_results:
        results.update(plugin_results)

    return results


def _find_query_candidate(profile: dict) -> str | None:
    """Find a good query candidate from profile directories."""
    from .gatherer import _scan_directories

    exclude = profile.get("exclude_patterns", [])
    files = _scan_directories(profile, exclude)
    if not files:
        return None
    # Pick first file, use its stem as query
    return files[0].stem


def _benchmark_plugins(profile: dict, output_dir: str) -> dict[str, dict[str, Any]]:
    """Benchmark with plugins if available."""
    results: dict[str, dict[str, Any]] = {}

    # Check tree-sitter availability
    try:
        import tree_sitter  # noqa: F401
        import tree_sitter_python  # noqa: F401

        results["structural-diff"] = _benchmark_structural_diff(profile, output_dir)
    except ImportError:
        pass

    # Check tiktoken availability
    try:
        from .tokenizer import _has_tiktoken

        if _has_tiktoken():
            results["tiktoken"] = _benchmark_tiktoken(profile, output_dir)
    except ImportError:
        pass

    return results


def _benchmark_structural_diff(profile: dict, output_dir: str) -> dict[str, Any]:
    """Benchmark structural diff with tree-sitter."""
    from .watcher import compute_diff as watcher_diff
    from .watcher import create_snapshot

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Create snapshot
    t0 = time.perf_counter()
    sid = create_snapshot(profile, name="bench-struct")
    create_time = time.perf_counter() - t0

    # Compute structural diff
    t0 = time.perf_counter()
    diffs = watcher_diff(sid, profile, fmt="markdown")
    diff_time = time.perf_counter() - t0

    from .differ_structural import structural_diff_sections

    t0 = time.perf_counter()
    struct_diffs = structural_diff_sections(diffs, "markdown")
    struct_time = time.perf_counter() - t0

    from .store import delete_snapshot

    delete_snapshot(sid)

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


def _benchmark_tiktoken(profile: dict, output_dir: str) -> dict[str, Any]:
    """Benchmark tiktoken token counting vs default."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Run full collect with default tokenizer
    default_result = _run_one(profile, output_dir, mode="full")

    # Run full collect with tiktoken
    p_tik = _make_profile(profile, tokenizer="tiktoken")
    t0 = time.perf_counter()
    created, tokens_by_file, parts = collect(
        p_tik, "Bench", str(out), mode="full", incremental=False
    )
    elapsed = time.perf_counter() - t0
    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
    from .collector import clean_manifest

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


def print_benchmark_table(results: dict[str, dict[str, Any]], fmt: str = "terminal"):
    """Print benchmark results as a formatted table."""
    if not results:
        print("No benchmark results.")
        return

    if fmt == "json":
        print(json.dumps(results, indent=2, default=str))
        return

    full = results.get("full", {})
    full_tokens = full.get("tokens", 1)
    full_time = full.get("time", 0.001)

    print()
    print("  Mode                  Parts     Tokens      Time       vs full tokens    vs full time")
    print("  " + "-" * 90)

    for mode, data in results.items():
        parts = data["parts"]
        tokens = data["tokens"]
        elapsed = data["time"]

        if mode == "full":
            token_pct = "baseline"
            time_pct = "baseline"
        elif full_tokens > 0:
            token_pct = f"{((tokens - full_tokens) / full_tokens * 100):+.1f}%"
            time_pct = f"{((elapsed - full_time) / full_time * 100):+.1f}%"
        else:
            token_pct = "—"
            time_pct = "—"

        detail = data.get("detail", {})
        detail_str = ""
        if detail:
            detail_str = "  " + ", ".join(f"{k}={v}" for k, v in detail.items())

        print(
            f"  {mode:22} {parts:5}   {tokens:>7}   {elapsed:.3f}s     {token_pct:>14}     {time_pct:>12}{detail_str}"
        )

    print()

    # Print summary
    savings = []
    if "repo-map" in results and full_tokens > 0:
        rm_tokens = results["repo-map"]["tokens"]
        pct = (full_tokens - rm_tokens) / full_tokens * 100
        savings.append(f"repo-map saves {pct:.0f}% tokens vs full")
    if "compress" in results and full_tokens > 0:
        cmp_tokens = results["compress"]["tokens"]
        pct = (full_tokens - cmp_tokens) / full_tokens * 100
        if pct > 0:
            savings.append(f"compress saves {pct:.1f}% tokens")
    if "incremental" in results:
        inc = results["incremental"]
        if inc["tokens"] == 0:
            savings.append(f"incremental: {inc['time'] * 1000:.0f}ms (no changes)")
    if "query" in results:
        q = results["query"]
        if full_tokens > 0:
            pct = (full_tokens - q["tokens"]) / full_tokens * 100
            savings.append(f"query saves {pct:.1f}% tokens")

    if savings:
        print("  Summary:")
        for s in savings:
            print(f"    • {s}")
        print()
