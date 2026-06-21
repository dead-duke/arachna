from arachna.config.core.config import find_config


def test_finds_in_cwd(tmp_path):
    (tmp_path / ".arachna.json").write_text("{}")
    assert find_config(root=tmp_path) is not None


def test_finds_in_parent(tmp_path):
    (tmp_path / ".arachna.json").write_text("{}")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert find_config(root=sub) is not None


def test_not_found(tmp_path):
    assert find_config(root=tmp_path) is None
