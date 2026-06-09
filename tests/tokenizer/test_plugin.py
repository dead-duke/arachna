import importlib
import sys
import tempfile
from pathlib import Path

from arachna.tokenizer import load_tokenizer


def test_load_default():
    tokenize = load_tokenizer("default")
    assert tokenize("hello world") == 2


def test_load_empty():
    tokenize = load_tokenizer("")
    assert tokenize("hello world") == 2


def test_load_custom_module():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "my_tok.py"
        f.write_text("def count_tokens(text: str) -> int:\n    return 999\n")
        sys.path.insert(0, d)
        try:
            tokenize = load_tokenizer("my_tok")
            assert tokenize("anything") == 999
        finally:
            sys.path.pop(0)
            importlib.invalidate_caches()
            if "my_tok" in sys.modules:
                del sys.modules["my_tok"]


def test_load_custom_module_with_function():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "my_tok2.py"
        f.write_text("def my_counter(text: str) -> int:\n    return len(text)\n")
        sys.path.insert(0, d)
        try:
            tokenize = load_tokenizer("my_tok2:my_counter")
            assert tokenize("hello") == 5
        finally:
            sys.path.pop(0)
            importlib.invalidate_caches()
            if "my_tok2" in sys.modules:
                del sys.modules["my_tok2"]
