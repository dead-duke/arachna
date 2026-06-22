"""Tests for _safe_local_imports in tokenizer.py."""

from arachna.domain.tokenization.tokenizer import _is_safe_tokenizer


def test_local_file_with_safe_imports(tmp_path):
    (tmp_path / "safe_tok.py").write_text(
        "import math\nfrom collections import defaultdict\ndef count_tokens(t): return 1\n"
    )
    assert _is_safe_tokenizer("safe_tok", root=tmp_path)


def test_local_file_with_unsafe_import_rejected(tmp_path):
    (tmp_path / "bad_tok.py").write_text("import os\ndef count_tokens(t): return 1\n")
    assert not _is_safe_tokenizer("bad_tok", root=tmp_path)


def test_local_file_with_unsafe_import_from_rejected(tmp_path):
    (tmp_path / "bad_tok2.py").write_text(
        "from subprocess import check_output\ndef count_tokens(t): return 1\n"
    )
    assert not _is_safe_tokenizer("bad_tok2", root=tmp_path)


def test_local_file_with_unsafe_nested_import_rejected(tmp_path):
    (tmp_path / "bad_tok3.py").write_text("import os.path\ndef count_tokens(t): return 1\n")
    assert not _is_safe_tokenizer("bad_tok3", root=tmp_path)


def test_local_file_with_syntax_error_rejected(tmp_path):
    (tmp_path / "syntax_err.py").write_text(
        "def count_tokens(t):\n    return 1\nthis is not valid python {{{{{\n"
    )
    assert not _is_safe_tokenizer("syntax_err", root=tmp_path)


def test_local_file_empty_allowed(tmp_path):
    (tmp_path / "empty.py").write_text("")
    assert _is_safe_tokenizer("empty", root=tmp_path)


def test_local_file_with_tiktoken_import_allowed(tmp_path):
    (tmp_path / "tiktoken_tok.py").write_text("import tiktoken\ndef count_tokens(t): return 1\n")
    assert _is_safe_tokenizer("tiktoken_tok", root=tmp_path)


def test_local_file_with_transformers_import_allowed(tmp_path):
    (tmp_path / "hf_tok.py").write_text(
        "from transformers import AutoTokenizer\ndef count_tokens(t): return 1\n"
    )
    assert _is_safe_tokenizer("hf_tok", root=tmp_path)
