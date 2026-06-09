"""Token estimation for AI models.

Default: 4 chars ≈ 1 token (conservative, zero dependencies).
Supports pluggable tokenizers via tokenizer spec string.
chars_per_token configurable via profile field or ARACHNA_CHARS_PER_TOKEN env var.
"""

import ast as _ast
import importlib
import os as _os
import sys
from collections.abc import Callable
from pathlib import Path

_SAFE_TOKENIZERS = frozenset(
    _os.environ.get("ARACHNA_SAFE_TOKENIZERS", "tiktoken,transformers").split(",")
)

_DEFAULT_CHARS_PER_TOKEN = int(_os.environ.get("ARACHNA_CHARS_PER_TOKEN", "4"))

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


def _is_safe_tokenizer(spec: str) -> bool:
    if not spec or spec == "default":
        return True
    module_name = spec.split(":", 1)[0]
    if module_name in _SAFE_TOKENIZERS:
        return True
    if module_name in _SUSPICIOUS_MODULES:
        return False
    if module_name in sys.stdlib_module_names:
        return False
    paths_to_check = [Path.cwd()] + [Path(p) for p in sys.path if p]
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


def _safe_local_imports(filepath: Path) -> bool:
    if not _validate_top_level_statements(filepath):
        return False
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
    return True


def count_tokens(text: str, chars_per_token: int | None = None) -> int:
    if chars_per_token is None:
        chars_per_token = _DEFAULT_CHARS_PER_TOKEN
    if chars_per_token <= 0:
        chars_per_token = 4
    return max(1, len(text) // chars_per_token)


def load_tokenizer(spec: str, chars_per_token: int | None = None) -> Callable[[str], int]:
    if not spec or spec == "default":
        cpt = chars_per_token if chars_per_token is not None else _DEFAULT_CHARS_PER_TOKEN
        return lambda text: count_tokens(text, chars_per_token=cpt)
    if not _is_safe_tokenizer(spec):
        raise ValueError(
            f"Unsafe tokenizer: '{spec}'. "
            f"Only 'default', safe modules ({', '.join(sorted(_SAFE_TOKENIZERS))}), "
            f"or local .py files with safe imports are allowed."
        )
    if ":" in spec:
        module_name, func_name = spec.split(":", 1)
    else:
        module_name = spec
        func_name = "count_tokens"
    mod = importlib.import_module(module_name)
    return getattr(mod, func_name)
