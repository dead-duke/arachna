"""Token estimation for AI models.

Default: 4 chars ≈ 1 token (conservative, zero dependencies).
Supports pluggable tokenizers via tokenizer spec string.
"""

import importlib
import sys
from collections.abc import Callable
from pathlib import Path

# Whitelist of known safe tokenizer modules.
# These are well-known libraries that provide token counting.
_SAFE_TOKENIZERS = frozenset({"tiktoken", "transformers"})

# Modules with suspicious names (common attack vectors) — always blocked.
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


def _is_safe_tokenizer(spec: str) -> bool:
    """Check if a tokenizer spec is safe to import.

    A spec is safe if:
    - It's "default" or empty (built-in)
    - The module name is in the whitelist (tiktoken, transformers)
    - The module is a local .py file in the current directory or sys.path
      (user-provided tokenizer in the project)

    Returns False for:
    - System modules like os, subprocess, sys, etc.
    - Stdlib modules that shouldn't be used as tokenizers
    - Suspicious module names (common attack vectors)
    - Non-existent modules that aren't local files
    """
    if not spec or spec == "default":
        return True

    module_name = spec.split(":", 1)[0]

    # Whitelist check — these are known safe tokenizer libraries
    if module_name in _SAFE_TOKENIZERS:
        return True

    # Block modules with suspicious names (common attack vectors)
    if module_name in _SUSPICIOUS_MODULES:
        return False

    # Block stdlib modules — they shouldn't be used as tokenizers
    if module_name in sys.stdlib_module_names:
        return False

    # Check if the module is a local file: try cwd + sys.path
    paths_to_check = [Path.cwd()] + [Path(p) for p in sys.path if p]
    try:
        for base in paths_to_check:
            local_path = base / f"{module_name}.py"
            if local_path.is_file():
                return True
            local_pkg = base / module_name
            if local_pkg.is_dir() and (local_pkg / "__init__.py").is_file():
                return True
    except OSError:
        pass

    # Allow if module is already loaded (installed package), reject otherwise
    return module_name in sys.modules


def count_tokens(text: str) -> int:
    """Conservative estimate: 4 chars ≈ 1 token."""
    return max(1, len(text) // 4)


def load_tokenizer(spec: str) -> Callable[[str], int]:
    """Load tokenizer from spec string.

    Spec formats:
        "default" or ""  → built-in conservative estimate
        "module:function" → importlib.import_module("module").function(text)
        "module"          → importlib.import_module("module").count_tokens(text)

    Only safe tokenizers are allowed:
    - Built-in "default"
    - Whitelisted: tiktoken, transformers
    - Local .py files in the current directory or sys.path

    Examples:
        "default"
        "tiktoken:cl100k_base"
        "my_tokenizer"          # my_tokenizer.py in project root
        "my_tokenizer:my_count"  # my_tokenizer.my_count(text)

    Raises:
        ValueError: if the tokenizer spec is not safe to import.
    """
    if not spec or spec == "default":
        return count_tokens

    if not _is_safe_tokenizer(spec):
        raise ValueError(
            f"Unsafe tokenizer: '{spec}'. "
            f"Only 'default', tiktoken, transformers, or local .py files are allowed."
        )

    if ":" in spec:
        module_name, func_name = spec.split(":", 1)
    else:
        module_name = spec
        func_name = "count_tokens"

    mod = importlib.import_module(module_name)
    return getattr(mod, func_name)
