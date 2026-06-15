"""Tests for .arachna_metrics.json and PipelineMetrics in collector.py."""

import json

from arachna.collector import collect


def test_metrics_file_written(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    out = tmp_path / "out"
    out.mkdir()

    created, tokens_by_file, parts, metrics = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
        },
        "P",
        str(out),
        root=tmp_path,
    )

    assert metrics is not None
    assert metrics.files_read >= 1
    assert metrics.extract_time_ms >= 0
    assert metrics.transform_time_ms >= 0
    assert metrics.load_time_ms >= 0
    assert metrics.tokens_raw > 0
    assert metrics.tokens_compressed > 0
    # compression_ratio can be > 1.0 for small files due to title/toc overhead

    metrics_file = out / ".arachna_metrics.json"
    assert metrics_file.exists()
    data = json.loads(metrics_file.read_text())
    assert data["files_read"] >= 1
    assert data["tokens_raw"] > 0
    assert "extract_time_ms" in data
    assert "transform_time_ms" in data
    assert "load_time_ms" in data
    assert "compression_ratio" in data


def test_metrics_empty_collection(tmp_path):
    src = tmp_path / "empty"
    src.mkdir()
    out = tmp_path / "out"
    out.mkdir()

    created, tokens_by_file, parts, metrics = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["empty"],
            "patterns": ["*.py"],
        },
        "P",
        str(out),
        root=tmp_path,
    )

    assert metrics is not None
    assert metrics.files_read == 0
    assert metrics.tokens_raw == 0
    assert metrics.tokens_compressed == 0
    assert metrics.compression_ratio == 1.0

    metrics_file = out / ".arachna_metrics.json"
    assert metrics_file.exists()


def test_metrics_with_compress(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("a\n\n\n\nb\n")
    out = tmp_path / "out"
    out.mkdir()

    created, tokens_by_file, parts, metrics = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
            "compress": True,
        },
        "P",
        str(out),
        root=tmp_path,
    )

    assert metrics is not None
    assert metrics.files_read >= 1
    assert metrics.tokens_raw > 0
    assert metrics.tokens_compressed > 0


def test_metrics_with_pre_commands(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    out = tmp_path / "out"
    out.mkdir()

    created, tokens_by_file, parts, metrics = collect(
        {
            "name_template": "c",
            "title_template": "# T (part {part})\n\n",
            "max_tokens": 16000,
            "split_mode": "by_file",
            "directories": ["src"],
            "patterns": ["*.py"],
            "pre_commands": ["echo 'tree output'"],
        },
        "P",
        str(out),
        root=tmp_path,
    )

    assert metrics is not None
    assert metrics.files_read >= 1
    assert metrics.tokens_raw > 0
