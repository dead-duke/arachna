"""Benchmark: parallel vs sequential collect (v3.6.0).

Parallel I/O is opt-in via ARACHNA_MAX_WORKERS (default 1).
This benchmark compares sequential (workers=1) vs parallel (workers=4)
across different file sizes and counts.
"""

import os
import time

import pytest

from arachna.domain.collector import collect


def _make_small_files(tmp_path, count):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(count):
        (src / f"file_{i}.py").write_text(
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


def _make_large_files(tmp_path, count, size_kb=100):
    src = tmp_path / "src"
    src.mkdir()
    content = "x" * (size_kb * 1024)
    for i in range(count):
        (src / f"large_{i}.py").write_text(f"# Large file {i}\n{content}")


def _make_mixed_files(tmp_path, small_count, large_count, large_size_kb=100):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(small_count):
        (src / f"small_{i}.py").write_text(f"# Small {i}\nprint('hello')\n")
    content = "x" * (large_size_kb * 1024)
    for i in range(large_count):
        (src / f"large_{i}.py").write_text(f"# Large file {i}\n{content}")


def _profile(**kw):
    return {
        "name_template": "bench",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 0,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*"],
        "use_gitignore": False,
        **kw,
    }


def _run_collect(tmp_path, profile, workers=None):
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    if workers is not None:
        os.environ["ARACHNA_MAX_WORKERS"] = str(workers)
    try:
        t0 = time.perf_counter()
        created, tokens_by_file, parts, metrics = collect(
            profile, "B", str(out), mode="full", root=tmp_path
        )
        elapsed = time.perf_counter() - t0
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            os.environ.pop("ARACHNA_MAX_WORKERS", None)

    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
    return {
        "files": len(created),
        "parts": len(parts),
        "tokens": total_tokens,
        "time": elapsed,
    }


def _bench(name, tmp_path, profile, workers_list=(1, 2, 4, 8)):
    results = {}
    for w in workers_list:
        _run_collect(tmp_path, profile, workers=w)
        r = _run_collect(tmp_path, profile, workers=w)
        results[w] = r["time"]

    baseline = results[1]
    parts = [f"{name}:"]
    for w in workers_list:
        t = results[w]
        speedup = baseline / t if t > 0 else 0
        parts.append(f"  workers={w}: {t:.4f}s (speedup {speedup:.2f}x)")
    print("\n" + "\n".join(parts))


@pytest.mark.benchmark
def test_bench_small_10(tmp_path):
    _make_small_files(tmp_path, 10)
    _bench("10 small files", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_small_100(tmp_path):
    _make_small_files(tmp_path, 100)
    _bench("100 small files", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_small_1000(tmp_path):
    _make_small_files(tmp_path, 1000)
    _bench("1000 small files", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_small_5000(tmp_path):
    _make_small_files(tmp_path, 5000)
    _bench("5000 small files", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_large_10_1mb(tmp_path):
    _make_large_files(tmp_path, 10, size_kb=1024)
    _bench("10 large files (1MB each)", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_large_50_100kb(tmp_path):
    _make_large_files(tmp_path, 50, size_kb=100)
    _bench("50 large files (100KB each)", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_large_200_50kb(tmp_path):
    _make_large_files(tmp_path, 200, size_kb=50)
    _bench("200 large files (50KB each)", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_large_500_10kb(tmp_path):
    _make_large_files(tmp_path, 500, size_kb=10)
    _bench("500 large files (10KB each)", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_mixed_100_small_10_large(tmp_path):
    _make_mixed_files(tmp_path, 100, 10, large_size_kb=500)
    _bench("100 small + 10 large (500KB)", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_mixed_500_small_50_large(tmp_path):
    _make_mixed_files(tmp_path, 500, 50, large_size_kb=200)
    _bench("500 small + 50 large (200KB)", tmp_path, _profile(patterns=["*.py"]))


@pytest.mark.benchmark
def test_bench_parallel_preserves_order(tmp_path):
    _make_small_files(tmp_path, 100)
    profile = _profile(patterns=["*.py"])

    out = tmp_path / "out"
    out.mkdir(exist_ok=True)

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "8"
    try:
        created, tokens_by_file, parts, metrics = collect(
            profile, "B", str(out), mode="full", root=tmp_path
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            os.environ.pop("ARACHNA_MAX_WORKERS", None)

    content = parts[0]
    idx_0 = content.index("file_0.py")
    idx_50 = content.index("file_50.py")
    idx_99 = content.index("file_99.py")
    assert idx_0 < idx_50 < idx_99, "Parallel I/O must preserve file order"
