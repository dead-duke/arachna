"""Tests for new extensions in _EXT_LANG (v2.8.2)."""

from pathlib import Path

from arachna.domain.formatter import _EXT_LANG, lang_for_path


def test_hpp_extension():
    assert _EXT_LANG["hpp"] == "cpp"
    assert lang_for_path(Path("header.hpp")) == "cpp"


def test_cmake_extension():
    assert _EXT_LANG["cmake"] == "cmake"
    assert lang_for_path(Path("CMakeLists.cmake")) == "cmake"


def test_gradle_extension():
    assert _EXT_LANG["gradle"] == "groovy"
    assert lang_for_path(Path("build.gradle")) == "groovy"


def test_lock_extension():
    assert _EXT_LANG["lock"] == "text"
    assert lang_for_path(Path("package-lock.lock")) == "text"


def test_conf_extension():
    assert _EXT_LANG["conf"] == "ini"
    assert lang_for_path(Path("app.conf")) == "ini"
