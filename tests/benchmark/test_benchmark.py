"""Benchmarks for arachna — run: python -m pytest tests/benchmark/ -v -s"""

import sys
import time
from pathlib import Path

from arachna.collector import collect


def _make_files(tmp_path: Path, count: int, content_fn=None):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(count):
        text = content_fn(i) if content_fn else _default_content(i)
        (src / f"file_{i}.py").write_text(text)


def _default_content(i):
    return (
        f"# Module {i}\n"
        f"import os\n\n"
        f"def function_{i}(x, y):\n"
        f'    """Docstring."""\n'
        f"    result = x + y\n"
        f"    return result * {i}\n\n"
        f"class Handler_{i}:\n"
        f"    def __init__(self):\n"
        f"        self.value = {i}\n"
        f"    def process(self, data):\n"
        f"        return data + self.value\n"
    )


def _content_with_blanks(i):
    return f"def f{i}():\n\n\n    x = {i}\n\n\n    return x\n\n\n"


def _profile(**kw):
    return {
        "name_template": "bench",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 32768,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
        **kw,
    }


def _run(tmp_path, profile, mode="full", query=None, incremental=False):
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    t0 = time.perf_counter()
    created, tokens_by_file, parts = collect(
        profile, "B", str(out), mode=mode, query=query, incremental=incremental
    )
    elapsed = time.perf_counter() - t0
    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
    return {
        "files": len(created),
        "parts": len(parts),
        "tokens": total_tokens,
        "time": elapsed,
        "all_content": "".join(parts),
    }


def _print_result(label, r):
    print(f"\n  {label}: {r['parts']} parts, {r['tokens']} tokens, {r['time']:.3f}s")
    sys.stdout.flush()


def _print_compare(label1, r1, label2, r2):
    print(f"\n  {label1}: {r1['tokens']} tokens")
    print(f"  {label2}:   {r2['tokens']} tokens")
    sys.stdout.flush()


# ── full mode (streaming) ──────────────────────────────────────────


def test_bench_full_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000)
    _run(tmp_path, _profile(), "full")  # warm-up
    r = _run(tmp_path, _profile(), "full")
    _print_result("full 1000", r)
    for i in range(1000):
        assert f"file_{i}.py" in r["all_content"]
    assert r["tokens"] > 0


# ── repo-map mode (signatures only) ────────────────────────────────


def test_bench_repo_map_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000)
    r = _run(tmp_path, _profile(), "repo-map")
    _print_result("repo-map 1000", r)
    assert r["tokens"] > 0
    assert "return result *" not in r["all_content"], "repo-map should strip function bodies"
    assert "def function_" in r["all_content"], "repo-map should keep signatures"
    r_full = _run(tmp_path, _profile(), "full")
    assert r["tokens"] < r_full["tokens"], (
        f"repo-map tokens ({r['tokens']}) should be less than full ({r_full['tokens']})"
    )


# ── headers mode ───────────────────────────────────────────────────


def test_bench_headers_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000)
    r = _run(tmp_path, _profile(), "headers")
    _print_result("headers 1000", r)
    assert r["tokens"] > 0
    assert "deps:" in r["all_content"], "headers should include dependency headers"


# ── compress (files with blank lines) ──────────────────────────────


def test_bench_full_compress_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000, _content_with_blanks)
    r_no = _run(tmp_path, _profile(), "full")
    r_cmp = _run(tmp_path, _profile(compress=True), "full")
    _print_compare("full no-compress", r_no, "full +compress", r_cmp)
    assert r_cmp["tokens"] < r_no["tokens"], "compress should reduce tokens"


# ── query filter ───────────────────────────────────────────────────


def test_bench_query_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000)
    r_no = _run(tmp_path, _profile(), "full")
    _run(tmp_path, _profile(), "full", query="file_500")  # warm-up for query
    r_q = _run(tmp_path, _profile(), "full", query="file_500")
    print(f"\n  full no-query: {r_no['tokens']} tokens")
    print(f"  full +query:   {r_q['tokens']} tokens ({r_q['files']} files)")
    sys.stdout.flush()
    assert r_q["files"] > 0, "query should match some files"
    assert r_q["tokens"] < r_no["tokens"], "query should reduce output"


# ── 5000 files (streaming stays alive) ─────────────────────────────


def test_bench_full_5000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 5000)
    r = _run(tmp_path, _profile(), "full")
    _print_result("full 5000", r)
    assert r["tokens"] > 0


# ── incremental (unchanged) ────────────────────────────────────────


def test_bench_incremental_unchanged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 500)
    r1 = _run(tmp_path, _profile(), "full", incremental=True)
    assert r1["files"] >= 1

    r2 = _run(tmp_path, _profile(), "full", incremental=True)
    print(
        f"\n  incr unchanged 500: {r2['files']} files, {r2['time']:.4f}s (first: {r1['time']:.4f}s)"
    )
    sys.stdout.flush()
    assert r2["files"] == 0
