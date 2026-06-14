"""Stress tests for arachna benchmarks."""

import pytest

from .test_performance import _make_files, _profile, _run_with_memory


@pytest.mark.slow
@pytest.mark.benchmark
def test_bench_full_50000(tmp_path):
    _make_files(tmp_path, 50000)
    _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")  # warm-up
    r = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    print(
        f"\n  full 50000: {r['parts']} parts, {r['tokens']} tokens, "
        f"{r['time']:.3f}s, {r['rss_mb']:.1f} MB"
    )
    assert r["rss_mb"] < 250, f"Streaming failed: {r['rss_mb']:.1f} MB (expected < 250 MB)"


@pytest.mark.benchmark
def test_bench_large_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        (src / f"file_{i}.py").write_text("x" * (1024 * 1024), encoding="utf-8")
    _run_with_memory(tmp_path, _profile(patterns=["*.py"], max_tokens=8192), "full")  # warm-up
    r = _run_with_memory(tmp_path, _profile(patterns=["*.py"], max_tokens=8192), "full")
    print(f"\n  Large files (10 x 1MB): {r['parts']} parts, {r['time']:.3f}s, {r['rss_mb']:.1f} MB")
    assert r["parts"] > 1
    assert r["rss_mb"] < 250


@pytest.mark.benchmark
def test_bench_unicode(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(100):
        (src / f"cyrillic_{i}.py").write_text(
            f"# Модуль {i}\ndef функция_{i}():\n    return 'Привет мир'\n",
            encoding="utf-8",
        )
    for i in range(100):
        (src / f"cjk_{i}.py").write_text(
            f"# 模块 {i}\ndef 函数_{i}():\n    return '你好世界'\n",
            encoding="utf-8",
        )
    _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")  # warm-up
    r = _run_with_memory(tmp_path, _profile(patterns=["*.py"]), "full")
    print(f"\n  Unicode (100 Cyrillic + 100 CJK): {r['tokens']} tokens, {r['time']:.3f}s")
    assert r["tokens"] > 0
