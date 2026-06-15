"""Benchmarks for structural diff performance."""

import time

import pytest

from arachna.watch.differ_structural import structural_diff_for_lang

from .test_performance import _default_content, _js_content, _profile, _run_with_memory


@pytest.mark.benchmark
def test_bench_structural_diff_performance():
    old_py = _default_content(0)
    new_py = old_py.replace("x + y", "x * y")

    t0 = time.perf_counter()
    for _ in range(100):
        structural_diff_for_lang(old_py, new_py, "test.py", "python", "markdown")
    py_time = time.perf_counter() - t0

    print(f"\n  Python AST structural diff (100 iterations): {py_time:.3f}s")

    try:
        import tree_sitter_javascript  # noqa: F401

        old_js = _js_content(0)
        new_js = old_js.replace("useState", "useReducer")

        t0 = time.perf_counter()
        for _ in range(100):
            structural_diff_for_lang(old_js, new_js, "test.js", "javascript", "markdown")
        js_time = time.perf_counter() - t0

        print(f"  JS tree-sitter structural diff (100 iterations): {js_time:.3f}s")
        print(f"  Ratio: JS is {js_time / py_time:.2f}x slower than Python")
    except ImportError:
        print("  JS tree-sitter not installed — skipping")


@pytest.mark.benchmark
def test_bench_tree_sitter_js_1000(tmp_path):
    try:
        import tree_sitter_javascript  # noqa: F401
    except ImportError:
        pytest.skip("tree-sitter-javascript not installed")

    src = tmp_path / "src"
    src.mkdir()
    for i in range(1000):
        (src / f"file_{i}.js").write_text(_js_content(i), encoding="utf-8")

    _run_with_memory(tmp_path, _profile(patterns=["*.js"]), "full")  # warm-up
    r_full = _run_with_memory(tmp_path, _profile(patterns=["*.js"]), "full")
    print(
        f"\n  JS full 1000: {r_full['parts']} parts, {r_full['tokens']} tokens, "
        f"{r_full['time']:.3f}s, {r_full['rss_mb']:.1f} MB"
    )

    _run_with_memory(tmp_path, _profile(patterns=["*.js"]), "repo-map")  # warm-up
    r_repo = _run_with_memory(tmp_path, _profile(patterns=["*.js"]), "repo-map")
    print(
        f"  JS repo-map 1000: {r_repo['parts']} parts, {r_repo['tokens']} tokens, "
        f"{r_repo['time']:.3f}s"
    )

    assert r_repo["tokens"] < r_full["tokens"]


@pytest.mark.benchmark
def test_bench_collection_python_vs_js(tmp_path):
    src_py = tmp_path / "src_py"
    src_py.mkdir()
    for i in range(500):
        (src_py / f"file_{i}.py").write_text(_default_content(i), encoding="utf-8")
    _run_with_memory(
        tmp_path, _profile(patterns=["*.py"], directories=["src_py"]), "full"
    )  # warm-up
    r_py = _run_with_memory(tmp_path, _profile(patterns=["*.py"], directories=["src_py"]), "full")
    print(
        f"\n  Python collection 500: {r_py['parts']} parts, {r_py['tokens']} tokens, "
        f"{r_py['time']:.3f}s"
    )

    src_js = tmp_path / "src_js"
    src_js.mkdir()
    for i in range(500):
        (src_js / f"file_{i}.js").write_text(_js_content(i), encoding="utf-8")
    _run_with_memory(
        tmp_path, _profile(patterns=["*.js"], directories=["src_js"]), "full"
    )  # warm-up
    r_js = _run_with_memory(tmp_path, _profile(patterns=["*.js"], directories=["src_js"]), "full")
    print(
        f"  JS collection 500: {r_js['parts']} parts, {r_js['tokens']} tokens, {r_js['time']:.3f}s"
    )

    assert r_py["tokens"] > 0
    assert r_js["tokens"] > 0
