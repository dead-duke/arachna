"""Benchmark module — config layer.

Measures collection performance across modes (full, compress, repo-map,
headers, incremental, query). Plugin benchmarks (structural-diff, tiktoken)
live in snapshot/benchmarks.py — they depend on snapshot/ internals.
"""

import json
import time
from pathlib import Path
from typing import Any

from ..domain.collection.collector import clean_manifest, collect
from ..domain.path_utils import SafePath
from .profile_config import ProfileConfig


def make_profile(profile: ProfileConfig, **overrides) -> ProfileConfig:
    p = profile.to_dict()
    p.update(overrides)
    return _dict_to_profile(p)


def _dict_to_profile(d: dict) -> ProfileConfig:
    defaults = ProfileConfig()
    return ProfileConfig(
        name_template=d.get("name_template", defaults.name_template),
        title_template=d.get("title_template", defaults.title_template),
        max_tokens=d.get("max_tokens", defaults.max_tokens),
        split_mode=d.get("split_mode", defaults.split_mode),
        directories=d.get("directories", defaults.directories),
        patterns=d.get("patterns", defaults.patterns),
        files=d.get("files", defaults.files),
        exclude_patterns=d.get("exclude_patterns", defaults.exclude_patterns),
        pre_commands=d.get("pre_commands", defaults.pre_commands),
        post_commands=d.get("post_commands", defaults.post_commands),
        command=d.get("command"),
        section_format=d.get("section_format", defaults.section_format),
        compress=d.get("compress", defaults.compress),
        include_binary=d.get("include_binary", defaults.include_binary),
        binary_extensions=d.get("binary_extensions"),
        binary_max_mb=d.get("binary_max_mb", defaults.binary_max_mb),
        tokenizer=d.get("tokenizer", defaults.tokenizer),
        chars_per_token=d.get("chars_per_token"),
        line_numbers=d.get("line_numbers", defaults.line_numbers),
        extends=d.get("extends"),
        remote=d.get("remote", defaults.remote),
        use_gitignore=d.get("use_gitignore", defaults.use_gitignore),
        split_marker=d.get("split_marker", defaults.split_marker),
        _explicit_keys=set(d.keys()),
    )


def _run_one(
    profile: ProfileConfig,
    output_dir: str,
    root: Path,
    mode: str = "full",
    query: str | None = None,
    incremental: bool = False,
) -> dict[str, Any]:
    out = SafePath(root / output_dir, root)
    out.mkdir(parents=True, exist_ok=True)
    name_tmpl = f"bench-{mode}"
    p = make_profile(profile, name_template=name_tmpl)
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


def run_benchmark(profile: ProfileConfig, output_dir: str, root: Path) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    results["full"] = _run_one(profile, output_dir, root, mode="full")
    results["compress"] = _run_one(
        make_profile(profile, compress=True), output_dir, root, mode="full"
    )
    results["repo-map"] = _run_one(profile, output_dir, root, mode="repo-map")
    results["headers"] = _run_one(profile, output_dir, root, mode="headers")
    results["incremental"] = _run_one(profile, output_dir, root, mode="full", incremental=True)
    query = _find_query_candidate(profile, root=root)
    if query:
        results["query"] = _run_one(profile, output_dir, root, mode="full", query=query)
    return results


def _find_query_candidate(profile: ProfileConfig, root: Path) -> str | None:
    from ..domain.collection.gatherer_files import _scan_directories

    exclude = profile.exclude_patterns
    files = _scan_directories(profile, exclude, root=root)
    if not files:
        return None
    return files[0].stem


def _format_benchmark_row(mode, data, full_tokens, full_time):
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
    return f"  {mode:22} {parts:5}   {tokens:>7}   {elapsed:.3f}s     {token_pct:>14}     {time_pct:>12}{detail_str}"


def _format_benchmark_savings(results):
    full_tokens = results.get("full", {}).get("tokens", 0)
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
    return savings


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
        print(_format_benchmark_row(mode, data, full_tokens, full_time))
    print()
    savings = _format_benchmark_savings(results)
    if savings:
        print("  Summary:")
        for s in savings:
            print(f"    • {s}")
        print()
