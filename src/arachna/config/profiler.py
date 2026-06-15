# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Benchmark module for arachna v4.0.0 — config layer.

Measures collection performance across modes (full, compress, repo-map,
headers, incremental, query). Plugin benchmarks (structural-diff, tiktoken)
live in watch/benchmarks.py — they depend on watch/ internals.
"""

import json
import time
from pathlib import Path
from typing import Any

from ..domain.collector import clean_manifest, collect


def _make_profile(profile: dict, **overrides) -> dict:
    p = dict(profile)
    p.update(overrides)
    return p


def _run_one(
    profile: dict,
    output_dir: str,
    root: Path,
    mode: str = "full",
    query: str | None = None,
    incremental: bool = False,
) -> dict[str, Any]:
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


def run_benchmark(profile: dict, output_dir: str, root: Path) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    results["full"] = _run_one(profile, output_dir, root, mode="full")
    p_compress = _make_profile(profile, compress=True)
    results["compress"] = _run_one(p_compress, output_dir, root, mode="full")
    results["repo-map"] = _run_one(profile, output_dir, root, mode="repo-map")
    results["headers"] = _run_one(profile, output_dir, root, mode="headers")
    results["incremental"] = _run_one(profile, output_dir, root, mode="full", incremental=True)
    query = _find_query_candidate(profile)
    if query:
        results["query"] = _run_one(profile, output_dir, root, mode="full", query=query)
    return results


def _find_query_candidate(profile: dict) -> str | None:
    from ..domain.gatherer import _scan_directories

    exclude = profile.get("exclude_patterns", [])
    files = _scan_directories(profile, exclude, root=Path.cwd())
    if not files:
        return None
    return files[0].stem


def print_benchmark_table(results: dict[str, dict[str, Any]], fmt: str = "terminal"):
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
        detail_str = "  " + ", ".join(f"{k}={v}" for k, v in detail.items()) if detail else ""
        print(
            f"  {mode:22} {parts:5}   {tokens:>7}   {elapsed:.3f}s     {token_pct:>14}     {time_pct:>12}{detail_str}"
        )
    print()
    savings = []
    if "repo-map" in results and full_tokens > 0:
        pct = (full_tokens - results["repo-map"]["tokens"]) / full_tokens * 100
        savings.append(f"repo-map saves {pct:.0f}% tokens vs full")
    if "compress" in results and full_tokens > 0:
        pct = (full_tokens - results["compress"]["tokens"]) / full_tokens * 100
        if pct > 0:
            savings.append(f"compress saves {pct:.1f}% tokens")
    if "incremental" in results and results["incremental"]["tokens"] == 0:
        savings.append(f"incremental: {results['incremental']['time'] * 1000:.0f}ms (no changes)")
    if "query" in results and full_tokens > 0:
        pct = (full_tokens - results["query"]["tokens"]) / full_tokens * 100
        savings.append(f"query saves {pct:.1f}% tokens")
    if savings:
        print("  Summary:")
        for s in savings:
            print(f"    • {s}")
        print()
