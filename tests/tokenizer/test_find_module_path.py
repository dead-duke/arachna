"""Tests for _find_module_path and _import_local_module in tokenizer.py."""

from arachna.domain.tokenizer import _find_module_path, _import_local_module


def test_find_module_path_py_file(tmp_path):
    (tmp_path / "mymod.py").write_text("def count_tokens(t): return 1")
    filepath = _find_module_path("mymod", root=tmp_path)
    assert filepath is not None
    assert filepath.name == "mymod.py"


def test_find_module_path_package(tmp_path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("def count_tokens(t): return 1")
    filepath = _find_module_path("mypkg", root=tmp_path)
    assert filepath is not None
    assert filepath.name == "__init__.py"


def test_find_module_path_not_found(tmp_path):
    filepath = _find_module_path("nonexistent", root=tmp_path)
    assert filepath is None


def test_import_local_module(tmp_path):
    (tmp_path / "mymod.py").write_text("def count_tokens(t): return 42")
    filepath = _find_module_path("mymod", root=tmp_path)
    mod = _import_local_module("mymod", filepath)
    assert mod.count_tokens("anything") == 42


def test_import_local_module_package(tmp_path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("def count_tokens(t): return 99")
    filepath = _find_module_path("mypkg", root=tmp_path)
    mod = _import_local_module("mypkg", filepath)
    assert mod.count_tokens("anything") == 99
