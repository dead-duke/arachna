from arachna.presets import get_detected_summary


def test_get_detected_summary_python(tmp_path, monkeypatch):
    """get_detected_summary returns detected presets with their config."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")
    (tmp_path / "README.md").write_text("# Project")
    (tmp_path / ".git").mkdir()

    summary = get_detected_summary()
    assert "python" in summary
    assert summary["python"]["split_mode"] == "by_file"
    assert "src" in summary["python"]["dirs"]
    assert "git" in summary
    assert "docs" in summary


def test_get_detected_summary_empty(tmp_path, monkeypatch):
    """get_detected_summary returns empty dict for empty project."""
    monkeypatch.chdir(tmp_path)
    summary = get_detected_summary()
    assert summary == {}


def test_get_detected_summary_with_external(tmp_path, monkeypatch):
    """get_detected_summary includes external presets."""
    import json

    monkeypatch.chdir(tmp_path)
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
    summary = get_detected_summary(external_path=f)
    assert "my_game" in summary
    assert summary["my_game"]["patterns"] == ["*.lua"]
    assert "git" in summary


def test_get_detected_summary_external_override(tmp_path, monkeypatch):
    """External preset overrides built-in in detected summary."""
    import json

    monkeypatch.chdir(tmp_path)
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
    summary = get_detected_summary(external_path=f)
    assert "python" in summary
    assert summary["python"]["dirs"] == ["custom_src"]
    assert summary["python"]["max_tokens"] == 32000
