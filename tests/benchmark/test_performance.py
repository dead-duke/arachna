import json
import os
import time
from pathlib import Path

import psutil
import pytest

from arachna.config.profile_config import ProfileConfig
from arachna.domain.collector import collect

BASELINE_FILE = Path(__file__).parent / "baseline.json"
RESULTS = []


def _make_files(tmp_path: Path, count: int, content_fn=None):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(count):
        text = content_fn(i) if content_fn else _default_content(i)
        (src / f"file_{i}.py").write_text(text, encoding="utf-8")


def _default_content(i):
    return (
        f"# Module {i}\nimport os\n\ndef function_{i}(x, y):\n"
        f'    """Docstring."""\n    result = x + y\n    return result * {i}\n\n'
        f"class Handler_{i}:\n    def __init__(self):\n        self.value = {i}\n"
        f"    def process(self, data):\n        return data + self.value\n"
    )


def _content_with_blanks(i):
    return f"def f{i}():\n\n\n    x = {i}\n\n\n    return x\n\n\n"


def _js_content(i):
    return (
        f"// Module {i}\nimport {{ useState }} from 'react';\n\n"
        f"export function App{i}() {{\n    const [count, setCount] = useState(0);\n"
        f"    return <div>{{count}}</div>;\n}}\n\n"
        f"export class Component{i} extends React.Component {{\n"
        f"    render() {{\n        return <span>Hello</span>;\n    }}\n}}\n"
    )


def _profile(**kw):
    return ProfileConfig(
        **{
            "name_template": "bench",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 32768,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*"],
            "use_gitignore": False,
            **kw,
        }
    )


def _run_with_memory(tmp_path, profile, mode="full", query=None, incremental=False):
    process = psutil.Process()
    rss_before = process.memory_info().rss

    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    t0 = time.perf_counter()
    created, tokens_by_file, parts, _metrics = collect(
        profile, "B", str(out), mode=mode, query=query, incremental=incremental, root=tmp_path
    )
    elapsed = time.perf_counter() - t0

    rss_after = process.memory_info().rss
    peak_rss = max(rss_before, rss_after)

    total_tokens = sum(tokens_by_file.values()) if isinstance(tokens_by_file, dict) else 0
    throughput_files = len(created) / elapsed if elapsed > 0 else 0
    throughput_tokens = total_tokens / elapsed if elapsed > 0 else 0

    return {
        "files": len(created),
        "parts": len(parts),
        "tokens": total_tokens,
        "time": elapsed,
        "rss_mb": peak_rss / (1024 * 1024),
        "throughput_files": throughput_files,
        "throughput_tokens": throughput_tokens,
        "all_content": "".join(parts),
    }


def _check_regression(name: str, result: dict, tolerance: float = 2.0):
    if os.environ.get("CI"):
        return
    if not BASELINE_FILE.exists():
        return
    baseline = json.loads(BASELINE_FILE.read_text())
    if name not in baseline:
        return
    expected = baseline[name]
    for metric in ["time", "rss_mb"]:
        if metric in expected and metric in result:
            threshold = expected[metric] * (1 + tolerance)
            assert result[metric] <= threshold, (
                f"{name} {metric} regression: {result[metric]:.3f} > {threshold:.3f} "
                f"(baseline: {expected[metric]:.3f})"
            )
            min_threshold = expected[metric] * 0.1
            assert result[metric] >= min_threshold, (
                f"{name} {metric} suspiciously fast: {result[metric]:.3f} "
                f"< {min_threshold:.3f} (baseline: {expected[metric]:.3f})"
            )


def _collect_result(test_name: str, result: dict):
    baseline_data = {k: v for k, v in result.items() if k != "all_content"}
    RESULTS.append({"test": test_name, **baseline_data})


@pytest.mark.benchmark
def test_bench_full_1000(tmp_path):
    _make_files(tmp_path, 1000)
    _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    r = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    print(
        f"\n  full 1000: {r['time']:.3f}s, {r['rss_mb']:.1f} MB, "
        f"{r['throughput_files']:.0f} files/s, {r['throughput_tokens']:.0f} tokens/s"
    )
    _check_regression("full_1000", r)
    _collect_result("full_1000", r)
    for i in [0, 100, 500, 999]:
        assert f"file_{i}.py" in r["all_content"]
    assert r["tokens"] > 0


@pytest.mark.benchmark
def test_bench_repo_map_1000(tmp_path):
    _make_files(tmp_path, 1000)
    _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "repo-map")
    r = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "repo-map")
    print(
        f"\n  repo-map 1000: {r['time']:.3f}s, {r['rss_mb']:.1f} MB, "
        f"{r['throughput_files']:.0f} files/s"
    )
    _check_regression("repo_map_1000", r)
    _collect_result("repo_map_1000", r)
    assert r["tokens"] > 0
    assert "return result *" not in r["all_content"]
    assert "def function_" in r["all_content"]
    r_full = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    assert r["tokens"] < r_full["tokens"]


@pytest.mark.benchmark
def test_bench_headers_1000(tmp_path):
    _make_files(tmp_path, 1000)
    _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "headers")
    r = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "headers")
    print(
        f"\n  headers 1000: {r['time']:.3f}s, {r['rss_mb']:.1f} MB, "
        f"{r['throughput_files']:.0f} files/s"
    )
    _collect_result("headers_1000", r)
    assert r["tokens"] > 0
    assert "deps:" in r["all_content"]


@pytest.mark.benchmark
def test_bench_full_compress_1000(tmp_path):
    _make_files(tmp_path, 1000, _content_with_blanks)
    _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    r_no = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    r_cmp = _run_with_memory(tmp_path, _profile(patterns=["*.py"], compress=True), "full")
    print(f"\n  full no-compress: {r_no['tokens']} tokens")
    print(f"  full +compress:   {r_cmp['tokens']} tokens")
    assert r_cmp["tokens"] < r_no["tokens"]


@pytest.mark.benchmark
def test_bench_query_1000(tmp_path):
    _make_files(tmp_path, 1000)
    _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    r_no = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    r_q = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full", query="file_500")
    print(f"\n  full no-query: {r_no['tokens']} tokens")
    print(f"  full +query:   {r_q['tokens']} tokens ({r_q['files']} files)")
    assert r_q["files"] > 0
    assert r_q["tokens"] < r_no["tokens"]


@pytest.mark.benchmark
def test_bench_full_5000(tmp_path):
    _make_files(tmp_path, 5000)
    _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    r = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    print(
        f"\n  full 5000: {r['time']:.3f}s, {r['rss_mb']:.1f} MB, "
        f"{r['throughput_files']:.0f} files/s, {r['throughput_tokens']:.0f} tokens/s"
    )
    _check_regression("full_5000", r)
    _collect_result("full_5000", r)
    assert r["tokens"] > 0
    assert r["rss_mb"] < 300


@pytest.mark.benchmark
def test_bench_incremental_unchanged(tmp_path):
    _make_files(tmp_path, 500)
    r1 = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full", incremental=True)
    assert r1["files"] >= 1
    r2 = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full", incremental=True)
    print(
        f"\n  incr unchanged 500: {r2['files']} files, {r2['time']:.4f}s (first: {r1['time']:.4f}s)"
    )
    assert r2["files"] == 0
