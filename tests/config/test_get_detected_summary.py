from arachna.config.presets import get_detected_summary


def test_get_detected_summary_python(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / ".git").mkdir()
    summary = get_detected_summary(root=tmp_path)
    assert "python" in summary
    assert summary["python"]["split_mode"] == "by_file"
    assert "src" in summary["python"]["dirs"]
    assert "git" in summary
    assert "docs" in summary


def test_get_detected_summary_empty(tmp_path):
    summary = get_detected_summary(root=tmp_path)
    assert summary == {}


def test_get_detected_summary_with_external(tmp_path):
    import json

    (tmp_path / "game").mkdir()
    (tmp_path / "game" / "main.lua").write_text("x")
    (tmp_path / ".git").mkdir()

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_game": {
                    "dirs": ["game"],
                    "patterns": ["*.lua"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                    "detect": ["game"],
                }
            }
        )
    )
    summary = get_detected_summary(root=tmp_path, external_path=f)
    assert "my_game" in summary
    assert summary["my_game"]["patterns"] == ["*.lua"]
    assert "git" in summary


def test_get_detected_summary_external_override(tmp_path):
    import json

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / ".git").mkdir()

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "python": {
                    "dirs": ["custom_src"],
                    "patterns": ["*.py"],
                    "max_tokens": 32000,
                    "split_mode": "by_file",
                    "detect": ["src"],
                }
            }
        )
    )
    summary = get_detected_summary(root=tmp_path, external_path=f)
    assert "python" in summary
    assert summary["python"]["dirs"] == ["custom_src"]
    assert summary["python"]["max_tokens"] == 32000
