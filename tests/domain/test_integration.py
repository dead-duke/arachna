from pathlib import Path

from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.collector import collect
from arachna.domain.collection.gatherer import gather_files


def test_gitignore_excludes_matched_files(tmp_path):
    (tmp_path / ".gitignore").write_text("*.txt\nsecret.key\n")
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "debug.txt").write_text("some log")
    (tmp_path / "secret.key").write_text("top secret")

    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[str(tmp_path)],
        patterns=["*"],
        use_gitignore=True,
    )
    sections = gather_files(p, root=tmp_path)
    filenames = [Path(s.split("\n")[0].replace("### ", "")).name for s in sections]
    assert "main.py" in filenames
    assert ".gitignore" in filenames
    assert "debug.txt" not in filenames
    assert "secret.key" not in filenames


def test_gitignore_nested_patterns(tmp_path):
    (tmp_path / ".gitignore").write_text("*.txt\n")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / ".gitignore").write_text("*.csv\n")
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "debug.txt").write_text("root log")
    (sub / "nested.py").write_text("nested")
    (sub / "nested.csv").write_text("comma,separated")

    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[str(tmp_path)],
        patterns=["*"],
        use_gitignore=True,
    )
    sections = gather_files(p, root=tmp_path)
    filenames = [Path(s.split("\n")[0].replace("### ", "")).name for s in sections]
    assert "main.py" in filenames
    assert "nested.py" in filenames
    assert ".gitignore" in filenames
    assert "debug.txt" not in filenames


def test_gitignore_use_gitignore_false_includes_all(tmp_path):
    (tmp_path / ".gitignore").write_text("*.txt\n")
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "debug.txt").write_text("some log")

    p = ProfileConfig(
        name_template="c",
        title_template="# T\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[str(tmp_path)],
        patterns=["*"],
        use_gitignore=False,
    )
    sections = gather_files(p, root=tmp_path)
    filenames = [Path(s.split("\n")[0].replace("### ", "")).name for s in sections]
    assert "main.py" in filenames
    assert "debug.txt" in filenames


def test_gitignore_patterns_tracked_in_manifest(tmp_path):
    (tmp_path / ".gitignore").write_text("*.txt\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')")
    (tmp_path / "src" / "debug.txt").write_text("log")

    p = ProfileConfig(
        name_template="chat-test",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*"],
        use_gitignore=True,
    )

    created, _, _, _ = collect(p, "TestProject", "out", root=tmp_path)
    assert len(created) == 1
    full = Path(created[0]).read_text()
    assert "main.py" in full
    assert "debug.txt" not in full
