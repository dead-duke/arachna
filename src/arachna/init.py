"""Interactive .arachna.json bootstrap."""

import json
from pathlib import Path

_SEPARATOR = "-" * 50

_CODE_DIRS = ["src", "app", "lib", "pkg", "cmd", "internal", "scripts"]
_TEST_DIRS = ["tests", "test"]
_DOCS_DIRS = ["docs", "documentation", "data/prompts", "config/messages"]
_DOCS_FILES = ["README.md", "README_DEV.md", "TODO.md", "CHANGELOG.md", "Makefile"]
_CONFIG_FILES = [
    "package.json",
    "tsconfig.json",
    "go.mod",
    "Cargo.toml",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
]

_GIT_CMD = (
    "git log --reverse "
    "--format='=== COMMIT: %h ===%nTITLE: %s%n%nMESSAGE:%n%b%n%nCHANGES:%n' "
    "--stat"
)


def _detect_dir(path: str) -> bool:
    p = Path(path)
    return p.is_dir() and any(p.rglob("*.*"))


def _detect_file(path: str) -> bool:
    return Path(path).exists()


def _ask(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value if value else default


def _ask_yes(prompt: str, default: bool = True) -> bool:
    suffix = "Y/n" if default else "y/N"
    answer = input(f"{prompt} [{suffix}]: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def run_defaults(output_dir: str = "."):
    cwd = Path.cwd()
    project_name = cwd.resolve().name
    config = {
        "project_name": project_name,
        "output_dir": output_dir,
        "profiles": {},
    }

    code_dirs = [d for d in _CODE_DIRS if _detect_dir(d)]
    if code_dirs:
        config["profiles"]["code"] = {
            "split_mode": "by_file",
            "directories": code_dirs,
            "patterns": ["*.py", "*.js", "*.ts", "*.go", "*.rs"],
            "files": [f for f in _CONFIG_FILES if _detect_file(f)],
            "pre_commands": [
                f"tree -I '__pycache__|*.pyc|*.egg-info|venv|node_modules' {' '.join(code_dirs)}"
            ],
            "max_tokens": 16000,
        }

    test_dirs = [d for d in _TEST_DIRS if _detect_dir(d)]
    if test_dirs:
        config["profiles"]["tests"] = {
            "split_mode": "by_file",
            "directories": test_dirs,
            "patterns": ["*.py", "*.js", "*.ts", "*.go", "*.rs"],
            "pre_commands": [f"tree {' '.join(test_dirs)}"],
            "max_tokens": 16000,
        }

    docs_files = [f for f in _DOCS_FILES if _detect_file(f)]
    docs_dirs = [d for d in _DOCS_DIRS if _detect_dir(d)]
    if docs_files or docs_dirs:
        docs_profile = {
            "split_mode": "by_file",
            "files": docs_files,
            "max_tokens": 16000,
        }
        if docs_dirs:
            docs_profile["directories"] = docs_dirs
            docs_profile["patterns"] = ["*.md", "*.txt", "*.json"]
        config["profiles"]["docs"] = docs_profile

    config["profiles"]["git"] = {
        "split_mode": "by_marker",
        "split_marker": "\n=== COMMIT:",
        "command": _GIT_CMD,
        "max_tokens": 16000,
    }

    _write_config(cwd, config, output_dir)
    print(f"Profiles: {', '.join(config['profiles'].keys())}")


def run_interactive(output_dir: str = "."):
    cwd = Path.cwd()
    from .config import find_config

    existing = find_config()
    if existing:
        print(f"Found existing config: {existing}")
        if not _ask_yes("Overwrite?", default=False):
            print("Aborted.")
            return

    project_name = _ask("Project name", cwd.resolve().name)
    output_dir = _ask("Output directory", output_dir)
    max_tokens = int(_ask("Default max tokens", "16000"))

    print()
    print(_SEPARATOR)
    print("Detected:")
    print(_SEPARATOR)

    profiles = {}

    code_dirs = [d for d in _CODE_DIRS if _detect_dir(d)]
    code_files = [f for f in _CONFIG_FILES if _detect_file(f)]
    if code_dirs or code_files:
        print(f"  Code dirs: {', '.join(code_dirs) if code_dirs else '(none)'}")
        if code_files:
            print(f"  Code files: {', '.join(code_files)}")
        if _ask_yes("  Add 'code' profile?", default=True):
            code_profile = {"split_mode": "by_file", "max_tokens": max_tokens}
            if code_dirs:
                code_profile["directories"] = code_dirs
                code_profile["patterns"] = ["*.py", "*.js", "*.ts", "*.go", "*.rs"]
            if code_files:
                code_profile["files"] = code_files
            profiles["code"] = code_profile

    test_dirs = [d for d in _TEST_DIRS if _detect_dir(d)]
    if test_dirs:
        print(f"  Test dirs: {', '.join(test_dirs)}")
        if _ask_yes("  Add 'tests' profile?", default=True):
            profiles["tests"] = {
                "split_mode": "by_file",
                "directories": test_dirs,
                "patterns": ["*.py", "*.js", "*.ts", "*.go", "*.rs"],
                "max_tokens": max_tokens,
            }

    docs_files = [f for f in _DOCS_FILES if _detect_file(f)]
    docs_dirs = [d for d in _DOCS_DIRS if _detect_dir(d)]
    if docs_files or docs_dirs:
        print(f"  Docs files: {', '.join(docs_files) if docs_files else '(none)'}")
        print(f"  Docs dirs: {', '.join(docs_dirs) if docs_dirs else '(none)'}")
        if _ask_yes("  Add 'docs' profile?", default=True):
            docs_profile = {"split_mode": "by_file", "max_tokens": max_tokens}
            if docs_files:
                docs_profile["files"] = docs_files
            if docs_dirs:
                docs_profile["directories"] = docs_dirs
                docs_profile["patterns"] = ["*.md", "*.txt", "*.json"]
            profiles["docs"] = docs_profile

    print()
    if _ask_yes("Add 'git' history profile?", default=True):
        profiles["git"] = {
            "split_mode": "by_marker",
            "split_marker": "\n=== COMMIT:",
            "command": _GIT_CMD,
            "max_tokens": max_tokens,
        }

    config = {
        "project_name": project_name,
        "output_dir": output_dir,
        "profiles": profiles,
    }

    print()
    print(_SEPARATOR)
    print(json.dumps(config, indent=2))
    print(_SEPARATOR)

    if _ask_yes("Create this config?", default=True):
        _write_config(cwd, config, output_dir)


def _write_config(cwd: Path, config: dict, output_dir: str):
    cfg_path = cwd / ".arachna.json"
    cfg_path.write_text(json.dumps(config, indent=2) + "\n")
    print(f"Created {cfg_path}")

    out_path = cwd / output_dir
    out_path.mkdir(parents=True, exist_ok=True)
    print(f"Created {out_path}/")

    print("Done. Run 'arachna --all' to collect context.")
