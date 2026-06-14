"""Coverage for _generate_header with edge cases."""

from arachna.formatter import _generate_header


def test_header_python_empty_file(tmp_path):
    f = tmp_path / "empty.py"
    header = _generate_header(f, "", "python")
    assert header == ""


def test_header_python_no_imports_no_exports(tmp_path):
    f = tmp_path / "simple.py"
    text = "x = 1\ny = 2\n"
    header = _generate_header(f, text, "python")
    assert header == ""


def test_header_c_like_empty(tmp_path):
    f = tmp_path / "empty.js"
    header = _generate_header(f, "", "javascript")
    assert header == ""


def test_header_typescript_export_interface(tmp_path):
    f = tmp_path / "types.ts"
    text = "export interface Config {\n    port: number\n}\n"
    header = _generate_header(f, text, "typescript")
    assert "exports:" in header
    assert "Config" in header


def test_header_go_func(tmp_path):
    f = tmp_path / "main.go"
    text = 'import "fmt"\n\nfunc main() {\n    fmt.Println("hi")\n}\n'
    header = _generate_header(f, text, "go")
    assert "deps:" in header
    assert "fmt" in header
    assert "exports:" in header
    assert "main" in header


def test_header_php_class(tmp_path):
    f = tmp_path / "app.php"
    text = "<?php\n\nuse App\\Services\\Auth;\n\nclass UserController {\n    public function index() {}\n}\n"
    header = _generate_header(f, text, "php")
    assert "deps:" in header
    assert "App\\Services\\Auth" in header


def test_header_ruby_def(tmp_path):
    f = tmp_path / "user.rb"
    text = "require 'json'\n\ndef initialize(name)\n    @name = name\nend\n"
    header = _generate_header(f, text, "ruby")
    assert "deps:" in header
    assert "json" in header
    assert "exports:" in header
    assert "initialize" in header


def test_header_csharp_using(tmp_path):
    f = tmp_path / "app.cs"
    text = "using System;\nusing System.Collections.Generic;\n\npublic class Program {\n    public static void Main() {}\n}\n"
    header = _generate_header(f, text, "csharp")
    assert "deps:" in header
    assert "System" in header


def test_header_cpp_include(tmp_path):
    f = tmp_path / "main.cpp"
    text = '#include <iostream>\n#include "header.h"\n\nint main() {\n    return 0;\n}\n'
    header = _generate_header(f, text, "cpp")
    assert "deps:" in header
    assert "iostream" in header


def test_header_javascript_require(tmp_path):
    f = tmp_path / "app.js"
    text = "const fs = require('fs');\nconst path = require('path');\n\nmodule.exports = function() {};\n"
    header = _generate_header(f, text, "javascript")
    assert "deps:" in header
    assert "fs" in header
    assert "path" in header
