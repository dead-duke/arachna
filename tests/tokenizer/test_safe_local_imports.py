"""Tests for _safe_local_imports in tokenizer.py (v2.5.0)."""

from arachna.tokenizer import _is_safe_tokenizer


def test_local_file_with_safe_imports(tmp_path, monkeypatch):
    """Local .py file with only safe imports passes."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "safe_tok.py").write_text(
        "import math\nfrom collections import defaultdict\ndef count_tokens(t): return 1\n"
    )
    assert _is_safe_tokenizer("safe_tok")


def test_local_file_with_unsafe_import_rejected(tmp_path, monkeypatch):
    """Local .py file importing os is rejected."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad_tok.py").write_text("import os\ndef count_tokens(t): return 1\n")
    assert not _is_safe_tokenizer("bad_tok")


def test_local_file_with_unsafe_import_from_rejected(tmp_path, monkeypatch):
    """Local .py file with 'from subprocess import ...' is rejected."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad_tok2.py").write_text(
        "from subprocess import check_output\ndef count_tokens(t): return 1\n"
    )
    assert not _is_safe_tokenizer("bad_tok2")


def test_local_file_with_unsafe_nested_import_rejected(tmp_path, monkeypatch):
    """Local .py file importing os.path is rejected (os is suspicious)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad_tok3.py").write_text("import os.path\ndef count_tokens(t): return 1\n")
    assert not _is_safe_tokenizer("bad_tok3")


def test_local_file_with_syntax_error_rejected(tmp_path, monkeypatch):
    """Local .py file with SyntaxError is rejected."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "syntax_err.py").write_text(
        "def count_tokens(t):\n    return 1\nthis is not valid python {{{{{\n"
    )
    assert not _is_safe_tokenizer("syntax_err")


def test_local_file_empty_allowed(tmp_path, monkeypatch):
    """Empty .py file has no suspicious imports — allowed."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty.py").write_text("")
    assert _is_safe_tokenizer("empty")


def test_local_file_with_tiktoken_import_allowed(tmp_path, monkeypatch):
    """Local file importing tiktoken is allowed (tiktoken is not suspicious)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tiktoken_tok.py").write_text("import tiktoken\ndef count_tokens(t): return 1\n")
    assert _is_safe_tokenizer("tiktoken_tok")


def test_local_file_with_transformers_import_allowed(tmp_path, monkeypatch):
    """Local file importing transformers is allowed (not suspicious)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "hf_tok.py").write_text(
        "from transformers import AutoTokenizer\ndef count_tokens(t): return 1\n"
    )
    assert _is_safe_tokenizer("hf_tok")
