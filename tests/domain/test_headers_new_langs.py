"""Tests for _generate_header with Elixir, Lua, Haskell, Gleam."""

from arachna.domain.formatting.formatter import _generate_header


def test_header_elixir(tmp_path):
    f = tmp_path / "app.ex"
    text = (
        "defmodule MyApp do\n"
        "  use SomeLib\n"
        "\n"
        "  def hello do\n"
        "    :world\n"
        "  end\n"
        "\n"
        "  defp secret do\n"
        "    :hidden\n"
        "  end\n"
        "end\n"
    )
    header = _generate_header(f, text, "elixir")
    assert "deps:" in header
    assert "SomeLib" in header
    assert "exports:" in header
    assert "hello" in header


def test_header_lua(tmp_path):
    f = tmp_path / "main.lua"
    text = "function init()\n    return true\nend\n\nfunction cleanup()\n    return nil\nend\n"
    header = _generate_header(f, text, "lua")
    assert "exports:" in header
    assert "init" in header
    assert "cleanup" in header


def test_header_haskell(tmp_path):
    f = tmp_path / "Main.hs"
    text = (
        "import System.IO\n"
        "import Data.List\n"
        "\n"
        "main :: IO ()\n"
        'main = putStrLn "hello"\n'
        "\n"
        "process :: String -> String\n"
        "process = id\n"
    )
    header = _generate_header(f, text, "haskell")
    assert isinstance(header, str)


def test_header_gleam(tmp_path):
    f = tmp_path / "main.gleam"
    text = (
        "import gleam/io\n"
        "import gleam/list\n"
        "\n"
        "pub fn main() {\n"
        '  io.println("hello")\n'
        "}\n"
        "\n"
        "pub fn helper() {\n"
        "  list.map([1, 2], fn(x) { x + 1 })\n"
        "}\n"
    )
    header = _generate_header(f, text, "gleam")
    assert isinstance(header, str)
