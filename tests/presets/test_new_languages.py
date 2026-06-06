"""Tests for v2.2.0 new language presets — Go, Rust, Zig, Lua, Elixir, Haskell, Gleam."""

from arachna.presets import detect_presets, preset_to_profile


def test_detect_go(tmp_path, monkeypatch):
    """Go detected when go.mod exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module example")
    (tmp_path / "main.go").write_text("package main")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "go" in detected


def test_detect_go_main_only(tmp_path, monkeypatch):
    """Go detected with only main.go."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "main.go").write_text("package main")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "go" in detected


def test_preset_to_profile_go(tmp_path, monkeypatch):
    """Go preset converts to profile with correct fields."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "go.mod").write_text("module x")
    (tmp_path / "go.sum").write_text("sum")
    (tmp_path / "main.go").write_text("package main")
    profile = preset_to_profile("go")
    assert profile is not None
    assert profile["split_mode"] == "by_file"
    assert "*.go" in profile["patterns"]
    assert "go.mod" in profile["files"]


def test_detect_rust(tmp_path, monkeypatch):
    """Rust detected when Cargo.toml exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Cargo.toml").write_text("[package]")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.rs").write_text("fn main() {}")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "rust" in detected


def test_preset_to_profile_rust(tmp_path, monkeypatch):
    """Rust preset converts to profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "Cargo.toml").write_text("[package]")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.rs").write_text("fn main() {}")
    profile = preset_to_profile("rust")
    assert profile is not None
    assert "*.rs" in profile["patterns"]
    assert "src" in profile["directories"]


def test_detect_zig(tmp_path, monkeypatch):
    """Zig detected when build.zig exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "build.zig").write_text('const std = @import("std");')
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "zig" in detected


def test_preset_to_profile_zig(tmp_path, monkeypatch):
    """Zig preset converts to profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "build.zig").write_text('const std = @import("std");')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.zig").write_text("pub fn main() void {}")
    profile = preset_to_profile("zig")
    assert profile is not None
    assert "*.zig" in profile["patterns"]
    assert "build.zig" in profile["files"]


def test_detect_lua(tmp_path, monkeypatch):
    """Lua detected when src/ directory with .lua files exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.lua").write_text("print('hello')")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "lua" in detected


def test_preset_to_profile_lua(tmp_path, monkeypatch):
    """Lua preset converts to profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.lua").write_text("print('hello')")
    profile = preset_to_profile("lua")
    assert profile is not None
    assert "*.lua" in profile["patterns"]


def test_detect_elixir(tmp_path, monkeypatch):
    """Elixir detected when mix.exs exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mix.exs").write_text("defmodule MyApp.MixProject do")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "elixir" in detected


def test_preset_to_profile_elixir(tmp_path, monkeypatch):
    """Elixir preset converts to profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mix.exs").write_text("defmodule MyApp.MixProject do")
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "my_app.ex").write_text("defmodule MyApp do")
    profile = preset_to_profile("elixir")
    assert profile is not None
    assert "*.ex" in profile["patterns"]
    assert "*.exs" in profile["patterns"]


def test_detect_haskell_cabal(tmp_path, monkeypatch):
    """Haskell detected when .cabal file exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "my-project.cabal").write_text("name: my-project")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "haskell" in detected


def test_detect_haskell_stack(tmp_path, monkeypatch):
    """Haskell detected when stack.yaml exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "stack.yaml").write_text("resolver: lts-22.0")
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "haskell" in detected


def test_preset_to_profile_haskell(tmp_path, monkeypatch):
    """Haskell preset converts to profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "my-project.cabal").write_text("name: my-project")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Main.hs").write_text("module Main where")
    profile = preset_to_profile("haskell")
    assert profile is not None
    assert "*.hs" in profile["patterns"]


def test_detect_gleam(tmp_path, monkeypatch):
    """Gleam detected when gleam.toml exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "gleam.toml").write_text('name = "my_app"')
    (tmp_path / ".git").mkdir()
    detected = detect_presets()
    assert "gleam" in detected


def test_preset_to_profile_gleam(tmp_path, monkeypatch):
    """Gleam preset converts to profile."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "gleam.toml").write_text('name = "my_app"')
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.gleam").write_text("import gleam/io")
    profile = preset_to_profile("gleam")
    assert profile is not None
    assert "*.gleam" in profile["patterns"]
    assert "gleam.toml" in profile["files"]


def test_formatter_extensions_new_languages():
    """_EXT_LANG contains all new language extensions."""
    from arachna.formatter import _EXT_LANG

    assert _EXT_LANG["go"] == "go"
    assert _EXT_LANG["rs"] == "rust"
    assert _EXT_LANG["zig"] == "zig"
    assert _EXT_LANG["lua"] == "lua"
    assert _EXT_LANG["ex"] == "elixir"
    assert _EXT_LANG["exs"] == "elixir"
    assert _EXT_LANG["hs"] == "haskell"
    assert _EXT_LANG["lhs"] == "haskell"
    assert _EXT_LANG["gleam"] == "gleam"
