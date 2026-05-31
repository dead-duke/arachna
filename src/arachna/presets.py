"""Language and engine presets for arachna init."""

from pathlib import Path

_SEPARATOR = "-" * 50

# ── Detection helpers ──────────────────────────────────────────────


def _detect_dir(path: str) -> bool:
    p = Path(path)
    return p.is_dir() and any(p.rglob("*.*"))


def _detect_file(path: str) -> bool:
    return Path(path).exists()


# ── Git history command ─────────────────────────────────────────────

_GIT_CMD = (
    "git log --reverse "
    "--format='=== COMMIT: %h ===%nTITLE: %s%n%nMESSAGE:%n%b%n%nCHANGES:%n' "
    "--stat"
)

# ── Preset definitions ──────────────────────────────────────────────
# Each preset is a dict:
#   dirs: list[str]           directories to scan
#   patterns: list[str]       glob patterns for scanned dirs
#   files: list[str]          explicit files to include
#   pre_commands: list[str]   commands to run before collection
#   max_tokens: int           token limit per part
#   split_mode: str           "by_file" | "by_marker" | "by_paragraph" | "single"
#   split_marker: str | None  marker for "by_marker" mode
#   detect: list[str]         paths to check for auto-detection (dirs or files)

PRESETS: dict[str, dict] = {
    # ── Python ──
    "python": {
        "dirs": ["src", "app", "lib", "pkg", "scripts"],
        "patterns": ["*.py"],
        "files": ["pyproject.toml", "requirements.txt", "requirements-dev.txt"],
        "pre_commands": [
            "tree -I '__pycache__|*.pyc|*.egg-info|venv|node_modules' src app lib pkg scripts 2>/dev/null || true"
        ],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["src", "app", "lib", "pkg"],
    },
    # ── JavaScript / TypeScript ──
    "javascript": {
        "dirs": ["src", "app", "lib", "scripts"],
        "patterns": ["*.js", "*.ts", "*.jsx", "*.tsx"],
        "files": ["package.json", "tsconfig.json"],
        "pre_commands": [
            "tree -I 'node_modules|__pycache__|venv' src app lib scripts 2>/dev/null || true"
        ],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["package.json", "tsconfig.json"],
    },
    # ── Tests (Python / JS / Go / Rust) ──
    "tests": {
        "dirs": ["tests", "test"],
        "patterns": ["*.py", "*.js", "*.ts", "*.go", "*.rs"],
        "files": [],
        "pre_commands": ["tree tests test 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["tests", "test"],
    },
    # ── Documentation ──
    "docs": {
        "dirs": ["docs", "documentation", "data/prompts", "config/messages"],
        "patterns": ["*.md", "*.txt", "*.json"],
        "files": ["README.md", "README_DEV.md", "TODO.md", "CHANGELOG.md", "Makefile"],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["docs", "documentation", "README.md", "TODO.md"],
    },
    # ── Git history ──
    "git": {
        "dirs": [],
        "patterns": [],
        "files": [],
        "pre_commands": [_GIT_CMD],
        "max_tokens": 16000,
        "split_mode": "by_marker",
        "split_marker": "\n=== COMMIT:",
        "detect": [".git"],
    },
    # ── Configuration files (cross-language) ──
    "config": {
        "dirs": [],
        "patterns": [],
        "files": [
            "package.json",
            "tsconfig.json",
            "go.mod",
            "Cargo.toml",
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
        ],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": [],
    },
    # ── Godot Engine ──
    "godot": {
        "dirs": ["."],
        "patterns": ["*.gd", "*.tscn", "*.tres", "*.gdshader"],
        "files": ["project.godot"],
        "pre_commands": ["tree -I '.godot|__pycache__' 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["project.godot"],
    },
    # ── Unity ──
    "unity": {
        "dirs": ["Assets"],
        "patterns": ["*.cs", "*.unity", "*.prefab"],
        "files": [],
        "pre_commands": ["tree Assets 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["Assets"],
    },
    # ── C / C++ ──
    "c_cpp": {
        "dirs": ["src", "include"],
        "patterns": ["*.c", "*.cpp", "*.h", "*.hpp"],
        "files": ["CMakeLists.txt", "Makefile"],
        "pre_commands": ["tree src include 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["CMakeLists.txt", "src", "include"],
    },
    # ── C# ──
    "csharp": {
        "dirs": ["."],
        "patterns": ["*.cs", "*.csproj", "*.sln"],
        "files": [],
        "pre_commands": ["tree -I 'bin|obj|node_modules' 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["*.csproj", "*.sln"],
    },
    # ── Swift ──
    "swift": {
        "dirs": ["Sources", "Source", "src"],
        "patterns": ["*.swift"],
        "files": ["Package.swift"],
        "pre_commands": ["tree Sources Source src 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["Package.swift", "Sources", "Source"],
    },
    # ── Kotlin / Java ──
    "kotlin_java": {
        "dirs": ["src"],
        "patterns": ["*.kt", "*.java"],
        "files": ["build.gradle", "build.gradle.kts", "pom.xml"],
        "pre_commands": ["tree src 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["build.gradle", "build.gradle.kts", "pom.xml"],
    },
    # ── Ruby ──
    "ruby": {
        "dirs": ["lib", "app"],
        "patterns": ["*.rb"],
        "files": ["Gemfile", "Rakefile"],
        "pre_commands": ["tree lib app 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["Gemfile", "Rakefile"],
    },
    # ── PHP ──
    "php": {
        "dirs": ["src", "app", "public"],
        "patterns": ["*.php"],
        "files": ["composer.json"],
        "pre_commands": ["tree src app public 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["composer.json"],
    },
    # ── Docker ──
    "docker": {
        "dirs": [],
        "patterns": [],
        "files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
        "pre_commands": [],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    },
    # ── Terraform ──
    "terraform": {
        "dirs": ["."],
        "patterns": ["*.tf", "*.tfvars"],
        "files": [],
        "pre_commands": ["tree -I '.terraform|__pycache__' 2>/dev/null || true"],
        "max_tokens": 16000,
        "split_mode": "by_file",
        "detect": ["*.tf"],
    },
}


# ── Auto-detection ──────────────────────────────────────────────────


def detect_presets() -> list[str]:
    """Return names of presets detected in the current directory.

    Detection order determines profile order in generated config.
    Special presets:
      - "config" is always included if any config files exist
      - "git" is always included if .git exists
      - "tests" is included if test dirs exist
      - "docs" is included if doc dirs/files exist
    """
    detected: list[str] = []

    # Language/engine presets (mutually exclusive first-match wins for
    # the "primary code" slot, but we collect all detected)
    language_presets = [
        "python",
        "javascript",
        "godot",
        "unity",
        "c_cpp",
        "csharp",
        "swift",
        "kotlin_java",
        "ruby",
        "php",
        "terraform",
        "docker",
    ]

    for name in language_presets:
        preset = PRESETS[name]
        detect_paths = preset.get("detect", [])
        if _detect_any(detect_paths):
            detected.append(name)

    # Always detect tests, docs, config, git if relevant
    for name in ["tests", "docs"]:
        preset = PRESETS[name]
        if _detect_any(preset.get("detect", [])):
            detected.append(name)

    if _detect_any(PRESETS["config"]["files"]):
        detected.append("config")

    if _detect_any(PRESETS["git"]["detect"]):
        detected.append("git")

    return detected


def _detect_any(paths: list[str]) -> bool:
    """Return True if any path (dir or file) exists.

    Glob patterns (e.g. "*.csproj") are matched via Path.glob.
    """
    cwd = Path.cwd()
    for p in paths:
        if "*" in p or "?" in p:
            if list(cwd.glob(p)):
                return True
        elif _detect_dir(p) or _detect_file(p):
            return True
    return False


# ── Preset → profile helpers ────────────────────────────────────────


def preset_to_profile(name: str) -> dict | None:
    """Convert a preset to a profile dict suitable for .arachna.json.

    Returns None if preset not found.
    """
    preset = PRESETS.get(name)
    if preset is None:
        return None

    profile: dict = {
        "split_mode": preset["split_mode"],
        "max_tokens": preset["max_tokens"],
    }

    if preset["dirs"]:
        profile["directories"] = [d for d in preset["dirs"] if _detect_dir(d)]
    if preset["patterns"]:
        profile["patterns"] = preset["patterns"]
    if preset["files"]:
        profile["files"] = [f for f in preset["files"] if _detect_file(f)]
    if preset.get("split_marker"):
        profile["split_marker"] = preset["split_marker"]
    if preset["pre_commands"]:
        profile["pre_commands"] = preset["pre_commands"]

    # If this is the git preset with a command, use command mode
    if name == "git" and _GIT_CMD in preset["pre_commands"]:
        profile.pop("directories", None)
        profile.pop("patterns", None)
        profile.pop("files", None)
        profile.pop("pre_commands", None)
        profile["command"] = _GIT_CMD

    return profile


def get_detected_summary() -> dict[str, dict]:
    """Return {preset_name: preset_dict} for all detected presets.

    Used by run_interactive to show what was found.
    """
    detected_names = detect_presets()
    return {name: PRESETS[name] for name in detected_names}
