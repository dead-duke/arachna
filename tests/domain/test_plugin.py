import importlib
import sys
import tempfile
from pathlib import Path

from arachna.domain.tokenization.tokenizer import load_tokenizer


def test_load_default():
    tokenize = load_tokenizer("default", root=Path.cwd())
    assert tokenize("hello world") == 2


def test_load_empty():
    tokenize = load_tokenizer("", root=Path.cwd())
    assert tokenize("hello world") == 2


def test_load_custom_module():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "my_tok.py"
        f.write_text("def count_tokens(text: str) -> int:\n    return 999\n")
        sys.path.insert(0, d)
        try:
            tokenize = load_tokenizer("my_tok", root=Path(d))
            assert tokenize("anything") == 999
        finally:
            sys.path.pop(0)
            importlib.invalidate_caches()
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith("my_tok"):
                    del sys.modules[mod_name]


def test_load_custom_module_with_function():
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "my_tok2.py"
        f.write_text("def my_counter(text: str) -> int:\n    return len(text)\n")
        sys.path.insert(0, d)
        try:
            tokenize = load_tokenizer("my_tok2:my_counter", root=Path(d))
            assert tokenize("hello") == 5
        finally:
            sys.path.pop(0)
            importlib.invalidate_caches()
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith("my_tok2"):
                    del sys.modules[mod_name]
