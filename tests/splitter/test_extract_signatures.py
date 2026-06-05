"""Tests for extract_signatures in splitter.py."""

from arachna.splitter import extract_signatures


def test_repo_map_python(tmp_path):
    """Python: ast extracts signatures, strips bodies."""
    text = (
        "import os\n"
        "\n"
        "@dataclass\n"
        "class Config:\n"
        '    """Configuration handler."""\n'
        "    host: str = 'localhost'\n"
        "    port: int = 8080\n"
        "\n"
        "def calculate_total(items: list[Item]) -> Decimal:\n"
        '    """Calculate total price."""\n'
        "    total = 0\n"
        "    for item in items:\n"
        "        total += item.price\n"
        "    return total\n"
        "\n"
        "async def fetch_data(url: str) -> dict:\n"
        "    async with aiohttp.ClientSession() as session:\n"
        "        async with session.get(url) as resp:\n"
        "            return await resp.json()\n"
    )
    sigs = extract_signatures(text, "python")
    assert "class Config:" in sigs
    assert "@dataclass" in sigs
    assert "def calculate_total" in sigs
    assert "async def fetch_data" in sigs
    # Bodies stripped, only '...' placeholder
    assert "total = 0" not in sigs
    assert "aiohttp" not in sigs
    assert "..." in sigs


def test_repo_map_python_syntax_error():
    """Python with syntax error returns full text."""
    text = "def foo(:\n    pass\n"
    sigs = extract_signatures(text, "python")
    assert sigs == text


def test_repo_map_javascript():
    """JavaScript: regex extracts signatures."""
    text = (
        "import React from 'react';\n"
        "\n"
        "export function App() {\n"
        "    const [count, setCount] = useState(0);\n"
        "    return <div>{count}</div>;\n"
        "}\n"
        "\n"
        "export async function fetchUsers() {\n"
        "    const res = await fetch('/api/users');\n"
        "    return res.json();\n"
        "}\n"
        "\n"
        "export class UserProfile extends React.Component {\n"
        "    render() {\n"
        "        return <div>Profile</div>;\n"
        "    }\n"
        "}\n"
    )
    sigs = extract_signatures(text, "javascript")
    assert "export function App" in sigs
    assert "export async function fetchUsers" in sigs
    assert "export class UserProfile" in sigs
    # Bodies stripped
    assert "useState" not in sigs
    assert "fetch('/api/users')" not in sigs
    assert "render()" not in sigs


def test_repo_map_go():
    """Go: regex extracts signatures."""
    text = (
        "package main\n"
        "\n"
        "func main() {\n"
        '    fmt.Println("hello")\n'
        "}\n"
        "\n"
        "func calculateSum(a, b int) int {\n"
        "    return a + b\n"
        "}\n"
        "\n"
        "type Handler struct {\n"
        "    db *sql.DB\n"
        "}\n"
    )
    sigs = extract_signatures(text, "go")
    assert "func main()" in sigs
    assert "func calculateSum(a, b int) int" in sigs
    assert "type Handler struct" in sigs
    assert "fmt.Println" not in sigs
    assert "return a + b" not in sigs
    assert "db *sql.DB" not in sigs


def test_repo_map_ruby():
    """Ruby: regex extracts signatures."""
    text = (
        "def initialize(name)\n"
        "    @name = name\n"
        "end\n"
        "\n"
        "def self.from_json(data)\n"
        "    new(data['name'])\n"
        "end\n"
        "\n"
        "def valid?\n"
        "    !@name.nil?\n"
        "end\n"
    )
    sigs = extract_signatures(text, "ruby")
    assert "def initialize(name)" in sigs
    assert "def self.from_json(data)" in sigs
    assert "def valid?" in sigs
    assert "@name = name" not in sigs


def test_repo_map_unknown_language():
    """Unknown language returns full text."""
    text = "some content\nwith multiple lines\n"
    sigs = extract_signatures(text, "")
    assert sigs == text


def test_repo_map_empty():
    """Empty input returns empty."""
    sigs = extract_signatures("", "python")
    assert sigs == ""


def test_repo_map_no_signatures():
    """File with no functions/classes returns empty for C-like, full for unknown."""
    text = "just some text\nno functions here\n"
    sigs = extract_signatures(text, "rust")
    # Rust: no signatures found → returns full text as fallback
    assert sigs == text
