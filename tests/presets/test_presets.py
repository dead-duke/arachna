from pathlib import Path

from arachna.presets import (
    _detect_any,
    _detect_dir,
    _detect_file,
    detect_presets,
    preset_to_profile,
)

# ── _detect_dir ─────────────────────────────────────────────────────


def test_detect_dir_found(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "main.py").write_text("x")
    assert _detect_dir(str(d))


def test_detect_dir_empty(tmp_path):
    d = tmp_path / "empty"
    d.mkdir()
    assert not _detect_dir(str(d))


def test_detect_dir_not_found(tmp_path):
    assert not _detect_dir(str(tmp_path / "nope"))


# ── _detect_file ────────────────────────────────────────────────────


def test_detect_file_found(tmp_path):
    f = tmp_path / "README.md"
    f.write_text("x")
    assert _detect_file(str(f))


def test_detect_file_not_found(tmp_path):
    assert not _detect_file(str(tmp_path / "nope.txt"))


# ── _detect_any ─────────────────────────────────────────────────────


def test_detect_any_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    assert _detect_any(["src"])


def test_detect_any_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("x")
    assert _detect_any(["README.md"])


def test_detect_any_glob(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "test.csproj").write_text("x")
    assert _detect_any(["*.csproj"])


def test_detect_any_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert not _detect_any(["nonexistent_dir", "missing.txt"])


# ── detect_presets ──────────────────────────────────────────────────


def test_detect_python(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "python" in detected
    assert "git" in detected


def test_detect_javascript(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "javascript" in detected


def test_detect_godot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "project.godot").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "godot" in detected


def test_detect_unity(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Assets").mkdir()
    (tmp_path / "Assets" / "script.cs").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "unity" in detected


def test_detect_c_cpp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "CMakeLists.txt").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "c_cpp" in detected


def test_detect_csharp_glob(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "MyProject.csproj").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "csharp" in detected


def test_detect_swift(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Package.swift").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "swift" in detected


def test_detect_kotlin_java(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "build.gradle").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "kotlin_java" in detected


def test_detect_ruby(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Gemfile").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "ruby" in detected


def test_detect_php(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "composer.json").write_text("{}")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "php" in detected


def test_detect_docker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Dockerfile").write_text("FROM python")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "docker" in detected


def test_detect_terraform_glob(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "main.tf").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "terraform" in detected


def test_detect_tests(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "tests" in detected


def test_detect_docs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("x")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "docs" in detected


def test_detect_multiple(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "Dockerfile").write_text("FROM python")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "python" in detected
    assert "javascript" in detected
    assert "docker" in detected


# ── preset_to_profile ───────────────────────────────────────────────


def test_preset_to_profile_python(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    profile = preset_to_profile("python")
    assert profile is not None
    assert profile["split_mode"] == "by_file"
    assert "src" in profile["directories"]
    assert "*.py" in profile["patterns"]


def test_preset_to_profile_git(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    profile = preset_to_profile("git")
    assert profile is not None
    assert profile["split_mode"] == "by_marker"
    assert "command" in profile
    assert "directories" not in profile


def test_preset_to_profile_unknown():
    assert preset_to_profile("nonexistent") is None


def test_preset_to_profile_docker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Dockerfile").write_text("FROM python")
    (tmp_path / "docker-compose.yml").write_text("x")
    profile = preset_to_profile("docker")
    assert profile is not None
    assert "Dockerfile" in profile["files"]
    assert "docker-compose.yml" in profile["files"]


def test_preset_to_profile_filters_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = preset_to_profile("docs")
    assert profile is not None
    # Only existing files should be in the profile
    for f in profile.get("files", []):
        assert Path(f).exists()
