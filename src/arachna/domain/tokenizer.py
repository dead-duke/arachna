# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Token estimation for AI models.

Default: 4 chars ~ 1 token (conservative, zero dependencies).
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

_INIT_FILE = "__init__.py"


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


def _is_safe_by_name(module_name: str, safe_tokenizers: frozenset) -> bool | None:
    if module_name in safe_tokenizers:
        return True
    if module_name in _SUSPICIOUS_MODULES:
        return False
    if module_name in sys.stdlib_module_names:
        return False
    return None


def _find_local_module_path(module_name: str, root: Path) -> Path | None:
    paths_to_check = [root] + [Path(p) for p in sys.path if p]
    try:
        for base in paths_to_check:
            candidate = base / f"{module_name}.py"
            if candidate.is_file():
                return candidate
            candidate_pkg = base / module_name
            if candidate_pkg.is_dir() and (candidate_pkg / _INIT_FILE).is_file():
                return candidate_pkg / _INIT_FILE
    except OSError:
        pass
    return None


def _is_safe_tokenizer(spec: str, root: Path | None = None) -> bool:
    if not spec or spec == "default":
        return True
    if root is None:
        root = Path.cwd()
    module_name = spec.split(":", 1)[0]
    safe_tokenizers = _get_safe_tokenizers()
    result = _is_safe_by_name(module_name, safe_tokenizers)
    if result is not None:
        return result
    local_path = _find_local_module_path(module_name, root)
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
        if isinstance(node, _ast.Assign) and _has_call_in_assign(node):
            return False
    return True


def _has_call_in_assign(node):
    for child in _ast.walk(node.value):
        if isinstance(child, _ast.Call):
            return True
    for target in node.targets:
        for child in _ast.walk(target):
            if isinstance(child, _ast.Call):
                return True
    return False


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


_plugins_checked = False
_HAS_TIKTOKEN = False
_HAS_TRANSFORMERS = False


def _check_tokenizer_plugins():
    global _plugins_checked, _HAS_TIKTOKEN, _HAS_TRANSFORMERS
    if _plugins_checked:
        return
    _plugins_checked = True
    _HAS_TIKTOKEN = _try_import_quiet("tiktoken")
    _HAS_TRANSFORMERS = _try_import_quiet("transformers")


def _try_import_quiet(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


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
    return lambda text: len(enc.encode(text))


def _load_transformers(spec: str) -> Callable[[str], int]:
    from transformers import AutoTokenizer

    model_name = spec.split(":", 1)[1] if ":" in spec else "bert-base-uncased"
    tok = AutoTokenizer.from_pretrained(model_name)  # nosec B615 — opt-in plugin, user installs transformers
    return lambda text: len(tok.encode(text))


def _find_module_path(module_name: str, root: Path | None = None) -> Path | None:
    if root is None:
        root = Path.cwd()
    paths_to_check = [root] + [Path(p) for p in sys.path if p]
    for base in paths_to_check:
        candidate = base / f"{module_name}.py"
        if candidate.is_file():
            return candidate
        candidate_pkg = base / module_name
        if candidate_pkg.is_dir() and (candidate_pkg / _INIT_FILE).is_file():
            return candidate_pkg / _INIT_FILE
    return None


def _import_local_module(module_name: str, filepath: Path) -> object:
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, str(filepath))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def count_tokens(text: str, chars_per_token: int | None = None) -> int:
    if chars_per_token is None:
        chars_per_token = _get_default_chars_per_token()
    if chars_per_token <= 0:
        chars_per_token = 4
    return max(1, len(text) // chars_per_token)


def load_tokenizer(
    spec: str, chars_per_token: int | None = None, root: Path | None = None
) -> Callable[[str], int]:
    if not spec or spec == "default":
        cpt = chars_per_token if chars_per_token is not None else _get_default_chars_per_token()
        return lambda text: count_tokens(text, chars_per_token=cpt)
    if not _is_safe_tokenizer(spec, root=root):
        safe_tokenizers = _get_safe_tokenizers()
        raise ValueError(
            f"Unsafe tokenizer: '{spec}'. Only 'default', safe modules ({', '.join(sorted(safe_tokenizers))}), or local .py files with safe imports are allowed."
        )
    if spec.startswith("tiktoken"):
        if _has_tiktoken():
            return _load_tiktoken(spec)
        raise ValueError("tiktoken is not installed. Install it with: pip install tiktoken")
    if spec.startswith("transformers"):
        if _has_transformers():
            return _load_transformers(spec)
        raise ValueError("transformers is not installed. Install it with: pip install transformers")
    module_name, func_name = (spec.split(":", 1) + ["count_tokens"])[:2]
    filepath = _find_module_path(module_name, root=root)
    if filepath is not None:
        mod = _import_local_module(module_name, filepath)
        return getattr(mod, func_name)
    mod = importlib.import_module(module_name)
    return getattr(mod, func_name)
