"""Tests for _generate_header in formatter.py."""

from arachna.domain.formatting.formatter import _generate_header


def test_header_python_ast(tmp_path):
    f = tmp_path / "utils.py"
    text = (
        "import os\n"
        "from pathlib import Path\n"
        "from .cache import load_cache\n"
        "\n"
        "def validate_token(token: str) -> bool:\n"
        "    return len(token) > 0\n"
        "\n"
        "class AuthHandler:\n"
        "    def authenticate(self, user: str) -> bool:\n"
        "        pass\n"
    )
    header = _generate_header(f, text, "python")
    assert "deps:" in header
    assert "os" in header
    assert "pathlib" in header
    assert "cache" in header
    assert "exports:" in header
    assert "validate_token" in header
    assert "AuthHandler" in header


def test_header_python_syntax_error(tmp_path):
    f = tmp_path / "broken.py"
    text = "def foo(:\n    pass\n"
    header = _generate_header(f, text, "python")
    assert isinstance(header, str)


def test_header_python_import_comma(tmp_path):
    f = tmp_path / "multi.py"
    text = "import os, sys\nfrom pathlib import Path\n\ndef foo(): pass\n"
    header = _generate_header(f, text, "python")
    assert "deps:" in header
    assert "os" in header
    assert "sys" in header
    assert "pathlib" in header


def test_header_javascript(tmp_path):
    f = tmp_path / "main.js"
    text = (
        "import { useState } from 'react';\n"
        "import axios from 'axios';\n"
        "const fs = require('fs');\n"
        "\n"
        "export function App() {\n"
        "    return <div>Hello</div>;\n"
        "}\n"
        "\n"
        "export class Component {\n"
        "    render() {}\n"
        "}\n"
    )
    header = _generate_header(f, text, "javascript")
    assert "deps:" in header
    assert "react" in header
    assert "axios" in header
    assert "fs" in header
    assert "exports:" in header
    assert "App" in header
    assert "Component" in header


def test_header_typescript(tmp_path):
    f = tmp_path / "types.ts"
    text = (
        "import type { User } from './types';\n"
        "import { fetchData } from '@/utils/api';\n"
        "\n"
        "export interface UserData {\n"
        "    id: number;\n"
        "    name: string;\n"
        "}\n"
        "\n"
        "export async function loadUser(id: number): Promise<User> {\n"
        "    return fetchData(id);\n"
        "}\n"
    )
    header = _generate_header(f, text, "typescript")
    assert "deps:" in header
    assert "./types" in header
    assert "exports:" in header
    assert "UserData" in header
    assert "loadUser" in header


def test_header_php_use_statements(tmp_path):
    f = tmp_path / "UserController.php"
    text = (
        "<?php\n\n"
        "use App\\Models\\User;\n"
        "use Illuminate\\Http\\Request;\n"
        "use App\\Services\\AuthService;\n"
        "\n"
        "class UserController {\n"
        "    public function show(Request $request) {}\n"
        "}\n"
    )
    header = _generate_header(f, text, "php")
    assert "deps:" in header
    assert "App\\Models\\User" in header
    assert "Illuminate\\Http\\Request" in header
    assert "App\\Services\\AuthService" in header


def test_header_ruby(tmp_path):
    f = tmp_path / "helper.rb"
    text = (
        "require 'json'\n"
        "require_relative 'utils'\n"
        "\n"
        "def parse_config(path)\n"
        "    JSON.parse(File.read(path))\n"
        "end\n"
        "\n"
        "def self.cache_key(id)\n"
        '    "user:#{id}"\n'
        "end\n"
    )
    header = _generate_header(f, text, "ruby")
    assert "deps:" in header
    assert "json" in header
    assert "exports:" in header
    assert "parse_config" in header
    assert "cache_key" in header


def test_header_unknown_language(tmp_path):
    f = tmp_path / "data.xyz"
    text = "some unknown content"
    header = _generate_header(f, text, "")
    assert header == ""


def test_header_no_deps_no_exports(tmp_path):
    f = tmp_path / "empty.py"
    text = "x = 1\ny = 2\n"
    header = _generate_header(f, text, "python")
    assert header == ""


def test_header_go(tmp_path):
    f = tmp_path / "main.go"
    text = (
        'import "fmt"\n'
        'import "net/http"\n'
        "\n"
        "func main() {\n"
        '    fmt.Println("hello")\n'
        "}\n"
        "\n"
        "func handleRequest(w http.ResponseWriter, r *http.Request) {\n"
        '    w.Write([]byte("ok"))\n'
        "}\n"
    )
    header = _generate_header(f, text, "go")
    assert "deps:" in header
    assert "fmt" in header
    assert "net/http" in header
    assert "exports:" in header
    assert "main" in header
    assert "handleRequest" in header
