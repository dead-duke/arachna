"""Token estimation for AI models.

Default: 4 chars ≈ 1 token (conservative, zero dependencies).
Supports pluggable tokenizers via tokenizer spec string.
"""

import importlib
from collections.abc import Callable


def count_tokens(text: str) -> int:
    """Conservative estimate: 4 chars ≈ 1 token."""
    return max(1, len(text) // 4)


def load_tokenizer(spec: str) -> Callable[[str], int]:
    """Load tokenizer from spec string.

    Spec formats:
        "default" or ""  → built-in conservative estimate
        "module:function" → importlib.import_module("module").function(text)
        "module"          → importlib.import_module("module").count_tokens(text)

    Examples:
        "default"
        "tiktoken:cl100k_base"
        "my_tokenizer"          # my_tokenizer.count_tokens(text)
        "my_tokenizer:my_count"  # my_tokenizer.my_count(text)
    """
    if not spec or spec == "default":
        return count_tokens

    if ":" in spec:
        module_name, func_name = spec.split(":", 1)
    else:
        module_name = spec
        func_name = "count_tokens"

    mod = importlib.import_module(module_name)
    return getattr(mod, func_name)
