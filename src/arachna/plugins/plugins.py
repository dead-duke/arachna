# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Plugin system for arachna v4.0.0.

Optional dependencies for language-specific features:
- tree-sitter: accurate structural diff for JS/TS/Go
- tiktoken/transformers: accurate token counting

Core stays zero-dep. Plugins are opt-in per language.
"""

import os
import subprocess
import sys
from pathlib import Path

PLUGIN_DEPS = {
    "javascript": ["tree-sitter", "tree-sitter-javascript"],
    "typescript": ["tree-sitter", "tree-sitter-typescript"],
    "go": ["tree-sitter", "tree-sitter-go"],
    "tiktoken": ["tiktoken"],
}

PLUGIN_DESCRIPTIONS = {
    "javascript": "Tree-sitter structural diff for JavaScript",
    "typescript": "Tree-sitter structural diff for TypeScript",
    "go": "Tree-sitter structural diff for Go",
    "tiktoken": "Accurate token counting via tiktoken",
}

_ENV_CHECKS = [
    (lambda: "PIPX_HOME" in os.environ or ".local/pipx" in sys.executable, "pipx"),
    (lambda: "POETRY_ACTIVE" in os.environ or "POETRY_HOME" in os.environ, "poetry"),
    (lambda: "CONDA_PREFIX" in os.environ, "conda"),
    (
        lambda: (
            ".venv" in sys.executable
            and (Path(sys.executable).parent.parent / "pyvenv.cfg").exists()
        ),
        "uv",
    ),
    (
        lambda: (
            hasattr(sys, "real_prefix")
            or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        ),
        "venv",
    ),
]


def _detect_environment() -> str:
    for check, env_name in _ENV_CHECKS:
        if check():
            return env_name
    return "system"


def _has_pep668() -> bool:
    import sysconfig

    marker = Path(sysconfig.get_path("stdlib")) / "EXTERNALLY-MANAGED"
    return marker.exists()


def _is_installed(package: str) -> bool:
    try:
        __import__(package.replace("-", "_"))
        return True
    except ImportError:
        return False


def list_plugins() -> dict[str, dict]:
    result = {}
    for name, deps in PLUGIN_DEPS.items():
        installed = all(_is_installed(d) for d in deps)
        result[name] = {
            "description": PLUGIN_DESCRIPTIONS.get(name, ""),
            "installed": installed,
            "deps": deps,
        }
    return result


def _build_install_command(language: str, env: str) -> str | None:
    deps = PLUGIN_DEPS.get(language)
    if not deps:
        return None
    if env == "pipx":
        return f"pipx inject arachna {' '.join(deps)}"
    elif env == "poetry":
        return f"poetry add {' '.join(deps)}"
    elif env in ("uv", "venv", "conda"):
        return f"pip install {' '.join(deps)}"
    elif env == "system":
        if _has_pep668():
            return None
        return f"pip install {' '.join(deps)}"
    return None


def install_plugin(language: str, execute: bool = False) -> str:
    if language not in PLUGIN_DEPS:
        return f"Unknown plugin: '{language}'. Available: {', '.join(sorted(PLUGIN_DEPS.keys()))}"
    deps = PLUGIN_DEPS[language]
    if all(_is_installed(d) for d in deps):
        return f"Plugin '{language}' is already installed."
    env = _detect_environment()
    cmd = _build_install_command(language, env)
    if cmd is None and env == "system" and _has_pep668():
        lines = [
            "Cannot install: system Python is externally managed (PEP 668).",
            "",
            "Options:",
            "  1. python -m venv .venv && source .venv/bin/activate",
            "  2. pip install --break-system-packages " + " ".join(deps),
            "  3. pip install 'arachna[" + language + "]'",
        ]
        return "\n".join(lines)
    lines = [f"Environment: {env}"]
    if execute:
        lines.append(f"Installing {', '.join(deps)}...")
        try:
            subprocess.run(cmd.split() + deps, check=True)
            lines.append(f"Plugin '{language}' ready. Restart arachna.")
        except subprocess.CalledProcessError:
            lines.append(f"Installation failed. Run manually: {cmd}")
    else:
        lines.append(f"Run: {cmd}")
    return "\n".join(lines)


def uninstall_plugin(language: str) -> str:
    if language not in PLUGIN_DEPS:
        return f"Unknown plugin: '{language}'. Available: {', '.join(sorted(PLUGIN_DEPS.keys()))}"
    deps = PLUGIN_DEPS[language]
    if not any(_is_installed(d) for d in deps):
        return f"Plugin '{language}' is not installed."
    return f"To uninstall: pip uninstall -y {' '.join(deps)}"
