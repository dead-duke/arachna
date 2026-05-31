"""Test for BUG-004: c_cpp preset falsely detected in Python-only projects.

Tests that should pass after fix are marked xfail.
"""

import pytest

from arachna.presets import detect_presets


def test_c_cpp_detected_with_cmake(tmp_path, monkeypatch):
    """c_cpp should be detected when CMakeLists.txt exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.cpp").write_text("int main() { return 0; }")
    (tmp_path / ".git").mkdir()

    detected = detect_presets()
    assert "c_cpp" in detected, (
        f"c_cpp not detected in C++ project with CMakeLists.txt. Detected: {detected}"
    )


def test_python_and_cpp_together(tmp_path, monkeypatch):
    """When both Python and C++ files exist, both should be detected."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "main.cpp").write_text("int main() { return 0; }")
    (tmp_path / ".git").mkdir()

    detected = detect_presets()
    assert "python" in detected
    assert "c_cpp" in detected


@pytest.mark.xfail(reason="BUG-004: c_cpp falsely detected via detect: ['src']", strict=True)
def test_c_cpp_not_detected_in_python_project(tmp_path, monkeypatch):
    """c_cpp should not be detected when only src/ exists with .py files."""
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (tmp_path / ".git").mkdir()

    detected = detect_presets()
    assert "c_cpp" not in detected, (
        f"c_cpp falsely detected in Python-only project. Detected: {detected}"
    )


@pytest.mark.xfail(reason="BUG-004: c_cpp falsely detected with empty src/ directory", strict=True)
def test_c_cpp_not_detected_empty_src(tmp_path, monkeypatch):
    """c_cpp should not be detected with just empty src/ directory."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()

    detected = detect_presets()
    assert "c_cpp" not in detected, f"c_cpp falsely detected with empty src/. Detected: {detected}"
