"""Tests for PipelineMetrics edge cases — compress, incremental, empty, query, repo-map."""

import json
import math

from arachna.domain.collector import collect


def _profile(**kw):
    return {
        "name_template": "c",
        "title_template": "# T (part {part})\n\n",
        "max_tokens": 16000,
        "split_mode": "by_file",
        "directories": ["src"],
        "patterns": ["*.py"],
        "use_gitignore": False,
        **kw,
    }


def test_metrics_with_compress(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("a\n\n\n\nb\n")
    out = tmp_path / "out"
    out.mkdir()

    created, tokens_by_file, parts, metrics = collect(
        _profile(compress=True), "P", str(out), root=tmp_path
    )

    assert metrics is not None
    assert metrics.tokens_raw > 0
    assert metrics.tokens_compressed > 0
    assert metrics.files_read >= 1


def test_metrics_incremental_first_run(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")
    out = tmp_path / "out"
    out.mkdir()

    _, _, _, m1 = collect(_profile(), "P", str(out), root=tmp_path, incremental=True)
    assert m1.files_read >= 1

    _, _, _, m2 = collect(_profile(), "P", str(out), root=tmp_path, incremental=True)
    assert m2.files_read == 0


def test_metrics_incremental_modified(tmp_path):
    import time

    src = tmp_path / "src"
    src.mkdir()
    f = src / "main.py"
    f.write_text("original")
    out = tmp_path / "out"
    out.mkdir()

    collect(_profile(), "P", str(out), root=tmp_path, incremental=True)
    time.sleep(0.01)
    f.write_text("modified")
    _, _, _, m = collect(_profile(), "P", str(out), root=tmp_path, incremental=True)
    assert m.files_read >= 1


def test_metrics_empty_collection(tmp_path):
    src = tmp_path / "empty"
    src.mkdir()
    out = tmp_path / "out"
    out.mkdir()

    _, _, _, m = collect(_profile(directories=["empty"]), "P", str(out), root=tmp_path)
    assert m.files_read == 0
    assert m.tokens_raw == 0
    assert m.tokens_compressed == 0
    assert math.isclose(m.compression_ratio, 1.0)


def test_metrics_with_query(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "auth.py").write_text("def login(): pass")
    (src / "utils.py").write_text("def helper(): pass")
    out = tmp_path / "out"
    out.mkdir()

    _, _, _, m = collect(_profile(), "P", str(out), root=tmp_path, query="auth")
    assert m.files_read == 1


def test_metrics_with_repo_map(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def foo():\n    return 1\n")
    out = tmp_path / "out"
    out.mkdir()

    _, _, _, m = collect(_profile(), "P", str(out), root=tmp_path, mode="repo-map")
    assert m.files_read >= 1
    assert m.tokens_raw > 0


def test_metrics_file_written(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")
    out = tmp_path / "out"
    out.mkdir()

    collect(_profile(), "P", str(out), root=tmp_path)
    mf = out / ".arachna_metrics.json"
    assert mf.exists()
    data = json.loads(mf.read_text())
    assert data["files_read"] >= 1
    assert data["tokens_raw"] > 0
    assert "extract_time_ms" in data
    assert "transform_time_ms" in data
    assert "load_time_ms" in data


def test_metrics_with_pre_commands(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")
    out = tmp_path / "out"
    out.mkdir()

    _, _, _, m = collect(_profile(pre_commands=["echo hi"]), "P", str(out), root=tmp_path)
    assert m.files_read >= 1
    assert m.tokens_raw > 0
