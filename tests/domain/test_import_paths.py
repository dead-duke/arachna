"""Coverage for load_tokenizer import paths."""

import sys

from arachna.domain.tokenizer import _is_safe_tokenizer, load_tokenizer


def test_load_tokenizer_custom_chars_per_token():
    tok = load_tokenizer("default", chars_per_token=2)
    assert tok("abcdefgh") == 4


def test_load_tokenizer_local_file_no_colon(tmp_path):
    (tmp_path / "simple_tok.py").write_text("def count_tokens(t): return 42\n")
    sys.path.insert(0, str(tmp_path))
    try:
        tok = load_tokenizer("simple_tok")
        assert tok("anything") == 42
    finally:
        sys.path.pop(0)
        import importlib

        importlib.invalidate_caches()
        if "simple_tok" in sys.modules:
            del sys.modules["simple_tok"]


def test_is_safe_tokenizer_local_package(tmp_path):
    pkg = tmp_path / "tok_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("def count_tokens(t): return 1\n")
    assert _is_safe_tokenizer("tok_pkg", root=tmp_path)
