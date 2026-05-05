from arachna.splitter import _build_parts


def test_single_section():
    parts = _build_parts(["hello world"], max_tokens=100)
    assert parts == ["hello world"]


def test_multiple_fit():
    parts = _build_parts(["a", "b", "c"], max_tokens=100)
    assert len(parts) == 1


def test_exceed_limit():
    parts = _build_parts(["a" * 40, "b" * 40, "c" * 40], max_tokens=2)
    assert len(parts) == 3


def test_single_exceeds():
    parts = _build_parts(["a" * 100], max_tokens=1)
    assert len(parts) == 1


def test_exact_fit():
    parts = _build_parts(["aaaa", "bbbb"], max_tokens=2)
    assert len(parts) == 1


def test_empty_sections():
    parts = _build_parts(["", "  ", "\n"], max_tokens=100)
    assert len(parts) == 0


def test_mixed_sizes():
    parts = _build_parts(["small", "x" * 500, "medium", "y" * 500], max_tokens=10)
    assert len(parts) == 4
