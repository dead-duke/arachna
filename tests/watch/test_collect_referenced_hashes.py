"""TC-182: _collect_referenced_hashes extracts all SHA256 hashes from manifests."""

from arachna.watch.store import _collect_referenced_hashes


def test_collect_referenced_hashes_files():
    manifests = [{"files": {"a.py": "sha256:abc123", "b.py": "sha256:def456"}}]
    hashes = _collect_referenced_hashes(manifests)
    assert hashes == {"abc123", "def456"}


def test_collect_referenced_hashes_pre_commands():
    manifests = [{"files": {}, "pre_commands": {"pre: echo": "sha256:cmd111"}}]
    hashes = _collect_referenced_hashes(manifests)
    assert hashes == {"cmd111"}


def test_collect_referenced_hashes_command():
    manifests = [{"files": {}, "command": {"command output": "sha256:out222"}}]
    hashes = _collect_referenced_hashes(manifests)
    assert hashes == {"out222"}


def test_collect_referenced_hashes_all_fields():
    manifests = [
        {
            "files": {"a.py": "sha256:aaa111"},
            "pre_commands": {"pre: tree": "sha256:bbb222"},
            "command": {"command output": "sha256:ccc333"},
        },
        {"files": {"b.py": "sha256:ddd444"}},
    ]
    hashes = _collect_referenced_hashes(manifests)
    assert hashes == {"aaa111", "bbb222", "ccc333", "ddd444"}


def test_collect_referenced_hashes_duplicates():
    manifests = [
        {"files": {"a.py": "sha256:same", "b.py": "sha256:same"}},
        {"files": {"c.py": "sha256:same"}},
    ]
    hashes = _collect_referenced_hashes(manifests)
    assert hashes == {"same"}


def test_collect_referenced_hashes_empty():
    assert _collect_referenced_hashes([]) == set()


def test_collect_referenced_hashes_no_fields():
    manifests = [{"id": "test", "name": "test"}]
    assert _collect_referenced_hashes(manifests) == set()
