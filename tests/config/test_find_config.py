from arachna.config import find_config


def test_finds_in_cwd(tmp_path, monkeypatch):
    (tmp_path / ".arachna.json").write_text("{}")
    monkeypatch.chdir(tmp_path)
    assert find_config() is not None


def test_finds_in_parent(tmp_path, monkeypatch):
    (tmp_path / ".arachna.json").write_text("{}")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    assert find_config() is not None


def test_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert find_config() is None
