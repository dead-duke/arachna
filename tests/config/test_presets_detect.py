"""Tests for c_cpp preset detection in Python-only projects."""

from arachna.config.presets import detect_presets


def test_c_cpp_detected_with_cmake(tmp_path):
    (tmp_path / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.cpp").write_text("int main() { return 0; }")
    (tmp_path / ".git").mkdir()
    detected = detect_presets(root=tmp_path)
    assert "c_cpp" in detected, f"c_cpp not detected in C++ project. Detected: {detected}"


def test_python_and_cpp_together(tmp_path):
    (tmp_path / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.10)")
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "main.cpp").write_text("int main() { return 0; }")
    (tmp_path / ".git").mkdir()
    detected = detect_presets(root=tmp_path)
    assert "python" in detected
    assert "c_cpp" in detected


def test_c_cpp_not_detected_in_python_project(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (tmp_path / ".git").mkdir()
    detected = detect_presets(root=tmp_path)
    assert "c_cpp" not in detected, (
        f"c_cpp falsely detected in Python-only project. Detected: {detected}"
    )


def test_c_cpp_not_detected_empty_src(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()
    detected = detect_presets(root=tmp_path)
    assert "c_cpp" not in detected, f"c_cpp falsely detected with empty src/. Detected: {detected}"
