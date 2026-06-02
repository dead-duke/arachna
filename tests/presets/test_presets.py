import json
from pathlib import Path

from arachna.presets import (
    _detect_any,
    _detect_dir,
    _detect_file,
    _load_builtin_presets,
    detect_presets,
    get_all_presets,
    load_presets_from_file,
    preset_to_profile,
)

# ── _load_builtin_presets ──────────────────────────────────────────


def test_load_builtin_presets_has_all():
    """Built-in presets loaded from JSON files contain all expected presets."""
    presets = _load_builtin_presets()
    assert "python" in presets
    assert "javascript" in presets
    assert "godot" in presets
    assert "unity" in presets
    assert "unreal" in presets
    assert "c_cpp" in presets
    assert "csharp" in presets
    assert "swift" in presets
    assert "kotlin_java" in presets
    assert "ruby" in presets
    assert "php" in presets
    assert "docker" in presets
    assert "terraform" in presets
    assert "tests" in presets
    assert "docs" in presets
    assert "config" in presets
    assert "git" in presets


def test_load_builtin_presets_no_service_field():
    """Service field removed in v1.5.1 — presets are JSON-only now, no metadata."""
    presets = _load_builtin_presets()
    for name, preset in presets.items():
        assert "service" not in preset, f"Preset '{name}' has 'service' field — should be removed"


def test_load_builtin_presets_git_command():
    """Git preset has pre_commands with git log command."""
    presets = _load_builtin_presets()
    assert len(presets["git"]["pre_commands"]) == 1
    assert "git log" in presets["git"]["pre_commands"][0]


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


# ── detect_presets with explicit preset_name ────────────────────────


def test_detect_presets_explicit_valid(tmp_path, monkeypatch):
    """Explicit preset with matching detect-paths returns the preset."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "project.godot").write_text("x")
    detected = detect_presets(preset_name="godot")
    assert detected == ["godot"]


def test_detect_presets_explicit_no_match(tmp_path, monkeypatch):
    """Explicit preset without matching detect-paths returns empty list."""
    monkeypatch.chdir(tmp_path)
    detected = detect_presets(preset_name="godot")
    assert detected == []


def test_detect_presets_explicit_unknown(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    detected = detect_presets(preset_name="nonexistent")
    assert detected == []


def test_detect_presets_explicit_service_no_match(tmp_path, monkeypatch):
    """Service presets with explicit name validate detect-paths."""
    monkeypatch.chdir(tmp_path)
    detected = detect_presets(preset_name="git")
    assert detected == []


def test_detect_presets_explicit_service_with_match(tmp_path, monkeypatch):
    """Service presets with explicit name return preset when detect-path matches."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    detected = detect_presets(preset_name="git")
    assert detected == ["git"]


def test_detect_presets_explicit_override(tmp_path, monkeypatch):
    """Explicit preset with matching files skips auto-detection entirely."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x")
    (tmp_path / "Dockerfile").write_text("FROM python")
    (tmp_path / ".git").mkdir()
    detected = detect_presets(preset_name="docker")
    assert detected == ["docker"]


def test_detect_presets_explicit_config_no_detect_paths(tmp_path, monkeypatch):
    """Config preset has empty detect list — always allowed."""
    monkeypatch.chdir(tmp_path)
    detected = detect_presets(preset_name="config")
    assert detected == ["config"]


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
    for f in profile.get("files", []):
        assert Path(f).exists()


# ── load_presets_from_file ──────────────────────────────────────────


def test_load_presets_valid(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_preset": {
                    "dirs": ["src"],
                    "patterns": ["*.py"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                }
            }
        )
    )
    result = load_presets_from_file(f)
    assert "my_preset" in result
    assert result["my_preset"]["dirs"] == ["src"]
    assert result["my_preset"]["max_tokens"] == 8000


def test_load_presets_not_found(tmp_path):
    result = load_presets_from_file(tmp_path / "nonexistent.json")
    assert result == {}


def test_load_presets_invalid_json(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text("not json")
    result = load_presets_from_file(f)
    assert result == {}


def test_load_presets_not_object(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text(json.dumps(["list", "not", "object"]))
    result = load_presets_from_file(f)
    assert result == {}


def test_load_presets_skips_non_dict_preset(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text(json.dumps({"bad": "string_not_object"}))
    result = load_presets_from_file(f)
    assert result == {}


def test_load_presets_invalid_split_mode(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text(json.dumps({"bad": {"split_mode": "invalid", "max_tokens": 100}}))
    result = load_presets_from_file(f)
    assert "bad" not in result


def test_load_presets_zero_max_tokens(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text(json.dumps({"bad": {"split_mode": "by_file", "max_tokens": 0}}))
    result = load_presets_from_file(f)
    assert "bad" not in result


def test_load_presets_negative_max_tokens(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text(json.dumps({"bad": {"split_mode": "by_file", "max_tokens": -1}}))
    result = load_presets_from_file(f)
    assert "bad" not in result


def test_load_presets_unknown_keys_warning(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps({"ok": {"split_mode": "by_file", "max_tokens": 100, "unknown_field": "x"}})
    )
    result = load_presets_from_file(f)
    assert "ok" in result


def test_load_presets_non_list_fields_converted(tmp_path):
    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps({"ok": {"split_mode": "by_file", "max_tokens": 100, "dirs": "not_a_list"}})
    )
    result = load_presets_from_file(f)
    assert "ok" in result
    assert result["ok"]["dirs"] == []


def test_load_presets_unsafe_tokenizer_rejected(tmp_path):
    """External preset with unsafe tokenizer gets reset to 'default'."""
    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "bad_tok": {
                    "dirs": ["src"],
                    "patterns": ["*.py"],
                    "max_tokens": 100,
                    "split_mode": "by_file",
                    "tokenizer": "os:system",
                }
            }
        )
    )
    result = load_presets_from_file(f)
    assert "bad_tok" in result
    assert result["bad_tok"]["tokenizer"] == "default"


def test_load_presets_safe_tokenizer_allowed(tmp_path):
    """External preset with tiktoken tokenizer is allowed."""
    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "safe_tok": {
                    "dirs": ["src"],
                    "patterns": ["*.py"],
                    "max_tokens": 100,
                    "split_mode": "by_file",
                    "tokenizer": "tiktoken:cl100k_base",
                }
            }
        )
    )
    result = load_presets_from_file(f)
    assert "safe_tok" in result
    assert result["safe_tok"]["tokenizer"] == "tiktoken:cl100k_base"


def test_load_presets_default_tokenizer_unchanged(tmp_path):
    """Default tokenizer passes validation unchanged."""
    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "ok": {
                    "dirs": ["src"],
                    "patterns": ["*.py"],
                    "max_tokens": 100,
                    "split_mode": "by_file",
                    "tokenizer": "default",
                }
            }
        )
    )
    result = load_presets_from_file(f)
    assert result["ok"]["tokenizer"] == "default"


# ── get_all_presets ─────────────────────────────────────────────────


def test_get_all_presets_builtin():
    all_presets = get_all_presets(external_path="/nonexistent.json")
    assert "python" in all_presets
    assert "godot" in all_presets


def test_get_all_presets_merged(tmp_path):
    f = tmp_path / "custom.json"
    f.write_text(
        json.dumps(
            {
                "python": {
                    "dirs": ["custom_src"],
                    "patterns": ["*.py"],
                    "max_tokens": 32000,
                    "split_mode": "by_file",
                },
                "my_game": {
                    "dirs": ["game"],
                    "patterns": ["*.lua"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                },
            }
        )
    )
    all_presets = get_all_presets(external_path=f)
    assert all_presets["python"]["dirs"] == ["custom_src"]
    assert all_presets["python"]["max_tokens"] == 32000
    assert "my_game" in all_presets
    assert all_presets["my_game"]["patterns"] == ["*.lua"]


def test_get_all_presets_default_path():
    """get_all_presets with no args uses DEFAULT_PRESETS_PATH."""
    all_presets = get_all_presets()
    assert "python" in all_presets


# ── detect_presets with external ────────────────────────────────────


def test_detect_presets_with_external_custom(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "game").mkdir()
    (tmp_path / "game" / "main.lua").write_text("x")

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_game": {
                    "dirs": ["game"],
                    "patterns": ["*.lua"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                    "detect": ["game"],
                }
            }
        )
    )
    detected = detect_presets(external_path=f)
    assert "my_game" in detected
    assert "git" in detected


def test_preset_to_profile_external(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "game").mkdir()
    (tmp_path / "game" / "main.lua").write_text("x")

    f = tmp_path / "presets.json"
    f.write_text(
        json.dumps(
            {
                "my_game": {
                    "dirs": ["game"],
                    "patterns": ["*.lua"],
                    "max_tokens": 8000,
                    "split_mode": "by_file",
                }
            }
        )
    )
    profile = preset_to_profile("my_game", external_path=f)
    assert profile is not None
    assert profile["split_mode"] == "by_file"
    assert "game" in profile["directories"]
    assert "*.lua" in profile["patterns"]


# ── Unreal Engine ───────────────────────────────────────────────────


def test_detect_unreal(tmp_path, monkeypatch):
    """Unreal Engine preset detected when .uproject file exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "MyProject.uproject").write_text("{}")
    (tmp_path / "Source").mkdir()
    (tmp_path / "Source" / "MyClass.cpp").write_text("// C++")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "unreal" in detected


def test_preset_to_profile_unreal(tmp_path, monkeypatch):
    """Unreal preset converts to profile with correct fields."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "MyProject.uproject").write_text("{}")
    (tmp_path / "Source").mkdir()
    (tmp_path / "Source" / "MyClass.cpp").write_text("// C++")
    (tmp_path / "Content").mkdir()
    (tmp_path / "Content" / "texture.uasset").write_bytes(b"\x00")

    profile = preset_to_profile("unreal")
    assert profile is not None
    assert profile["split_mode"] == "by_file"
    assert profile["max_tokens"] == 16000
    assert "Source" in profile["directories"]
    assert "Content" in profile["directories"]
    assert "*.cpp" in profile["patterns"]
    assert "*.h" in profile["patterns"]
    assert "*.cs" in profile["patterns"]
    assert "*.ini" in profile["patterns"]
    assert "*.uproject" in profile["patterns"]
    assert "*.uplugin" in profile["patterns"]


def test_unreal_not_detected_without_uproject(tmp_path, monkeypatch):
    """Unreal preset not detected when no .uproject file."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Source").mkdir()
    (tmp_path / "Source" / "MyClass.cpp").write_text("// C++")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "unreal" not in detected


# ── No _SERVICE_PRESETS — all presets treated equally ───────────────


def test_no_service_presets_hardcoded():
    """_SERVICE_PRESETS should not exist in the module."""
    import arachna.presets as p

    assert not hasattr(p, "_SERVICE_PRESETS")


def test_no_presets_dict_hardcoded():
    """PRESETS dict should not exist — presets come from JSON files."""
    import arachna.presets as p

    assert not hasattr(p, "PRESETS")
