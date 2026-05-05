from arachna.splitter import _split_to_sections


def test_restores_marker():
    sections = _split_to_sections("one\n\n### two\n\n### three", "\n\n### ")
    assert sections == ["one", "\n\n### two", "\n\n### three"]


def test_no_marker():
    sections = _split_to_sections("hello world", "\n\n### ")
    assert sections == ["hello world"]


def test_empty():
    sections = _split_to_sections("", "\n\n### ")
    assert sections == []


def test_marker_at_start():
    sections = _split_to_sections("\n\n### first\n\n### second", "\n\n### ")
    assert sections == ["\n\n### first", "\n\n### second"]
