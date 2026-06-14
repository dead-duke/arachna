"""Tests for _is_safe_tokenizer — local .py file detection."""

import sys

from arachna.tokenizer import _is_safe_tokenizer


def test_local_py_file_in_cwd(tmp_path):
    (tmp_path / "my_tok.py").write_text("def count_tokens(t): return 1")
    assert _is_safe_tokenizer("my_tok", root=tmp_path)


def test_local_py_file_in_sys_path(tmp_path):
    lib = tmp_path / "lib"
    lib.mkdir()
    (lib / "my_tok.py").write_text("def count_tokens(t): return 1")
    sys.path.insert(0, str(lib))
    try:
        assert _is_safe_tokenizer("my_tok")
    finally:
        sys.path.pop(0)


def test_local_package_with_init(tmp_path):
    pkg = tmp_path / "my_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    assert _is_safe_tokenizer("my_pkg", root=tmp_path)


def test_nonexistent_module_denied(tmp_path):
    assert not _is_safe_tokenizer("nonexistent_tokenizer_xyz", root=tmp_path)


def test_stdlib_module_denied():
    assert not _is_safe_tokenizer("json")
    assert not _is_safe_tokenizer("pathlib")


def test_suspicious_module_denied():
    assert not _is_safe_tokenizer("os")
    assert not _is_safe_tokenizer("subprocess")
