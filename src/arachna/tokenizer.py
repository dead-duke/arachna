# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Token estimation for AI models.

Default: 4 chars ≈ 1 token (conservative, zero dependencies).
Supports pluggable tokenizers via tokenizer spec string.
chars_per_token configurable via profile field or ARACHNA_CHARS_PER_TOKEN env var.
Safe tokenizers list configurable via ARACHNA_SAFE_TOKENIZERS env var.
"""

import ast as _ast
import importlib
import os as _os
import sys
from collections.abc import Callable
from pathlib import Path


def _get_safe_tokenizers() -> frozenset:
    return frozenset(_os.environ.get("ARACHNA_SAFE_TOKENIZERS", "tiktoken,transformers").split(","))


def _get_default_chars_per_token() -> int:
    return int(_os.environ.get("ARACHNA_CHARS_PER_TOKEN", "4"))


_SUSPICIOUS_MODULES = frozenset(
    {
        "os",
        "subprocess",
        "sys",
        "shutil",
        "importlib",
        "builtins",
        "ctypes",
        "socket",
        "http",
        "urllib",
        "requests",
        "pickle",
        "base64",
        "code",
        "codeop",
        "compileall",
        "crypt",
        "curses",
        "email",
        "ftplib",
        "glob",
        "hashlib",
        "imaplib",
        "io",
        "json",
        "logging",
        "marshal",
        "multiprocessing",
        "pathlib",
        "pdb",
        "platform",
        "poplib",
        "posix",
        "pprint",
        "pty",
        "random",
        "re",
        "runpy",
        "shelve",
        "shlex",
        "signal",
        "smtplib",
        "sqlite3",
        "ssl",
        "struct",
        "tempfile",
        "textwrap",
        "threading",
        "time",
        "traceback",
        "uuid",
        "webbrowser",
        "xml",
        "zipfile",
        "zipimport",
    }
)


def _is_safe_tokenizer(spec: str, root: Path | None = None) -> bool:
    if not spec or spec == "default":
        return True

    if root is None:
        root = Path.cwd()

    module_name = spec.split(":", 1)[0]
    safe_tokenizers = _get_safe_tokenizers()

    if module_name in safe_tokenizers:
        return True

    if module_name in _SUSPICIOUS_MODULES:
        return False

    if module_name in sys.stdlib_module_names:
        return False

    paths_to_check = [root] + [Path(p) for p in sys.path if p]
    local_path = None
    try:
        for base in paths_to_check:
            candidate = base / f"{module_name}.py"
            if candidate.is_file():
                local_path = candidate
                break
            candidate_pkg = base / module_name
            if candidate_pkg.is_dir() and (candidate_pkg / "__init__.py").is_file():
                local_path = candidate_pkg / "__init__.py"
                break
    except OSError:
        pass

    if local_path is None:
        return False

    return _safe_local_imports(local_path)


_ALLOWED_TOP_LEVEL = (
    _ast.FunctionDef,
    _ast.AsyncFunctionDef,
    _ast.ClassDef,
    _ast.Import,
    _ast.ImportFrom,
    _ast.Assign,
)


def _validate_top_level_statements(filepath: Path) -> bool:
    try:
        tree = _ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return False

    for node in tree.body:
        if not isinstance(node, _ALLOWED_TOP_LEVEL):
            return False
        if isinstance(node, _ast.Assign):
            for child in _ast.walk(node.value):
                if isinstance(child, _ast.Call):
                    return False
            for target in node.targets:
                for child in _ast.walk(target):
                    if isinstance(child, _ast.Call):
                        return False

    return True


def _safe_local_imports(filepath: Path) -> bool:
    try:
        tree = _ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return False

    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _SUSPICIOUS_MODULES:
                    return False
        elif (
            isinstance(node, _ast.ImportFrom)
            and node.module
            and node.module.split(".")[0] in _SUSPICIOUS_MODULES
        ):
            return False

    return _validate_top_level_statements(filepath)


# ── Plugin checks — lazy on first use ────────────────────────────

_plugins_checked = False
_HAS_TIKTOKEN = False
_HAS_TRANSFORMERS = False


def _check_tokenizer_plugins():
    global _plugins_checked, _HAS_TIKTOKEN, _HAS_TRANSFORMERS
    if _plugins_checked:
        return
    _plugins_checked = True
    try:
        import tiktoken  # noqa: F401

        _HAS_TIKTOKEN = True
    except ImportError:
        pass

    try:
        import warnings

        _prev = _os.environ.get("TRANSFORMERS_VERBOSITY")
        _os.environ["TRANSFORMERS_VERBOSITY"] = "error"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import transformers  # noqa: F401
        _HAS_TRANSFORMERS = True
        if _prev is not None:
            _os.environ["TRANSFORMERS_VERBOSITY"] = _prev
    except ImportError:
        _HAS_TRANSFORMERS = False


def _has_tiktoken() -> bool:
    _check_tokenizer_plugins()
    return _HAS_TIKTOKEN


def _has_transformers() -> bool:
    _check_tokenizer_plugins()
    return _HAS_TRANSFORMERS


def _load_tiktoken(spec: str) -> Callable[[str], int]:
    import tiktoken

    encoding_name = spec.split(":", 1)[1] if ":" in spec else "cl100k_base"
    enc = tiktoken.get_encoding(encoding_name)

    def _count(text: str) -> int:
        return len(enc.encode(text))

    return _count


def _load_transformers(spec: str) -> Callable[[str], int]:
    from transformers import AutoTokenizer

    model_name = spec.split(":", 1)[1] if ":" in spec else "bert-base-uncased"
    tok = AutoTokenizer.from_pretrained(model_name)

    def _count(text: str) -> int:
        return len(tok.encode(text))

    return _count


def count_tokens(text: str, chars_per_token: int | None = None) -> int:
    if chars_per_token is None:
        chars_per_token = _get_default_chars_per_token()
    if chars_per_token <= 0:
        chars_per_token = 4
    return max(1, len(text) // chars_per_token)


def load_tokenizer(spec: str, chars_per_token: int | None = None) -> Callable[[str], int]:
    if not spec or spec == "default":
        cpt = chars_per_token if chars_per_token is not None else _get_default_chars_per_token()
        return lambda text: count_tokens(text, chars_per_token=cpt)

    if not _is_safe_tokenizer(spec):
        safe_tokenizers = _get_safe_tokenizers()
        raise ValueError(
            f"Unsafe tokenizer: '{spec}'. "
            f"Only 'default', safe modules ({', '.join(sorted(safe_tokenizers))}), "
            f"or local .py files with safe imports are allowed."
        )

    if spec.startswith("tiktoken"):
        if _has_tiktoken():
            return _load_tiktoken(spec)
        raise ValueError("tiktoken is not installed. Install it with: pip install tiktoken")

    if spec.startswith("transformers"):
        if _has_transformers():
            return _load_transformers(spec)
        raise ValueError("transformers is not installed. Install it with: pip install transformers")

    if ":" in spec:
        module_name, func_name = spec.split(":", 1)
    else:
        module_name = spec
        func_name = "count_tokens"

    mod = importlib.import_module(module_name)
    return getattr(mod, func_name)
