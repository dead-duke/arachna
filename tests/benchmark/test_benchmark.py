"""Benchmarks for arachna — run: python -m pytest tests/benchmark/ -v -s"""

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


def _js_content(i):
    return (
        f"// Module {i}\n"
        f"import {{ useState }} from 'react';\n\n"
        f"export function App{i}() {{\n"
        f"    const [count, setCount] = useState(0);\n"
        f"    return <div>{{count}}</div>;\n"
        f"}}\n\n"
        f"export class Component{i} extends React.Component {{\n"
        f"    render() {{\n"
        f"        return <span>Hello</span>;\n"
        f"    }}\n"
        f"}}\n"
    )


def _profile(**kw):
    return {
        "name_template": "bench",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 32768,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*"],
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


# ── full mode (streaming) ──────────────────────────────────────────


def test_bench_full_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000)
    _run(tmp_path, _profile(patterns=["*.py"]), "full")  # warm-up
    r = _run(tmp_path, _profile(patterns=["*.py"]), "full")
    print(f"\n  full 1000: {r['parts']} parts, {r['tokens']} tokens, {r['time']:.3f}s")
    for i in range(1000):
        assert f"file_{i}.py" in r["all_content"]
    assert r["tokens"] > 0


# ── repo-map mode ─────────────────────────────────────────────────


def test_bench_repo_map_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000)
    r = _run(tmp_path, _profile(patterns=["*.py"]), "repo-map")
    print(f"\n  repo-map 1000: {r['parts']} parts, {r['tokens']} tokens, {r['time']:.3f}s")
    assert r["tokens"] > 0
    assert "return result *" not in r["all_content"]
    assert "def function_" in r["all_content"]
    r_full = _run(tmp_path, _profile(patterns=["*.py"]), "full")
    assert r["tokens"] < r_full["tokens"]


# ── headers mode ───────────────────────────────────────────────────


def test_bench_headers_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000)
    r = _run(tmp_path, _profile(patterns=["*.py"]), "headers")
    print(f"\n  headers 1000: {r['parts']} parts, {r['tokens']} tokens, {r['time']:.3f}s")
    assert r["tokens"] > 0
    assert "deps:" in r["all_content"]


# ── compress ───────────────────────────────────────────────────────


def test_bench_full_compress_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000, _content_with_blanks)
    r_no = _run(tmp_path, _profile(patterns=["*.py"]), "full")
    r_cmp = _run(tmp_path, _profile(patterns=["*.py"], compress=True), "full")
    print(f"\n  full no-compress: {r_no['tokens']} tokens")
    print(f"  full +compress:   {r_cmp['tokens']} tokens")
    assert r_cmp["tokens"] < r_no["tokens"]


# ── query ──────────────────────────────────────────────────────────


def test_bench_query_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 1000)
    r_no = _run(tmp_path, _profile(patterns=["*.py"]), "full")
    r_q = _run(tmp_path, _profile(patterns=["*.py"]), "full", query="file_500")
    print(f"\n  full no-query: {r_no['tokens']} tokens")
    print(f"  full +query:   {r_q['tokens']} tokens ({r_q['files']} files)")
    assert r_q["files"] > 0
    assert r_q["tokens"] < r_no["tokens"]


# ── 5000 files ─────────────────────────────────────────────────────


def test_bench_full_5000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 5000)
    r = _run(tmp_path, _profile(patterns=["*.py"]), "full")
    print(f"\n  full 5000: {r['parts']} parts, {r['tokens']} tokens, {r['time']:.3f}s")
    assert r["tokens"] > 0


# ── incremental ────────────────────────────────────────────────────


def test_bench_incremental_unchanged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_files(tmp_path, 500)
    r1 = _run(tmp_path, _profile(patterns=["*.py"]), "full", incremental=True)
    assert r1["files"] >= 1
    r2 = _run(tmp_path, _profile(patterns=["*.py"]), "full", incremental=True)
    print(
        f"\n  incr unchanged 500: {r2['files']} files, {r2['time']:.4f}s (first: {r1['time']:.4f}s)"
    )
    assert r2["files"] == 0


# ── plugin: tree-sitter JS ────────────────────────────────────────


def test_bench_tree_sitter_js_1000(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    for i in range(1000):
        (src / f"file_{i}.js").write_text(_js_content(i))

    r_full = _run(tmp_path, _profile(patterns=["*.js"]), "full")
    print(
        f"\n  tree-sitter JS full 1000: {r_full['parts']} parts, {r_full['tokens']} tokens, {r_full['time']:.3f}s"
    )
    assert r_full["tokens"] > 0

    r_struct = _run(tmp_path, _profile(patterns=["*.js"]), "headers")
    print(
        f"  tree-sitter JS headers 1000: {r_struct['parts']} parts, {r_struct['tokens']} tokens, {r_struct['time']:.3f}s"
    )
    assert r_struct["tokens"] > 0


# ── structural diff comparison ─────────────────────────────────────


def test_bench_structural_diff_comparison(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    src_py = tmp_path / "src_py"
    src_py.mkdir()
    for i in range(500):
        (src_py / f"file_{i}.py").write_text(_default_content(i))
    r_py = _run(tmp_path, _profile(patterns=["*.py"], directories=["src_py"]), "full")
    print(
        f"\n  Python AST structural 500: {r_py['parts']} parts, {r_py['tokens']} tokens, {r_py['time']:.3f}s"
    )

    src_js = tmp_path / "src_js"
    src_js.mkdir()
    for i in range(500):
        (src_js / f"file_{i}.js").write_text(_js_content(i))
    r_js = _run(tmp_path, _profile(patterns=["*.js"], directories=["src_js"]), "full")
    print(
        f"  JS tree-sitter/regex 500: {r_js['parts']} parts, {r_js['tokens']} tokens, {r_js['time']:.3f}s"
    )

    assert r_py["tokens"] > 0
    assert r_js["tokens"] > 0
