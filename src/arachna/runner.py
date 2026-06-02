"""Safe command execution with sandbox validation and audit logging."""

import json
import logging
import re
import shlex
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("arachna.runner")

# Shell metacharacters that require shell=True
_SHELL_CHARS = {"|", "&", ";", "<", ">", "$", "`", "(", ")", "{", "}"}

# Pipe separator for splitting piped commands
_PIPE_SEP = "|"

# Safe utilities that don't download/execute external code.
# Strictly read-only: no filesystem modifications.
_ALLOWED_COMMANDS = frozenset(
    {
        "echo",
        "cat",
        "ls",
        "tree",
        "find",
        "grep",
        "wc",
        "sort",
        "uniq",
        "head",
        "tail",
        "cut",
        "tr",
        "git",
        "hg",
        "svn",
        "date",
        "env",
        "pwd",
        "whoami",
        "id",
        "uname",
        "which",
        "diff",
        "comm",
        "join",
        "paste",
        "true",
        "false",
        "test",
        "[",
    }
)

# Dangerous command words/patterns — blocked by default.
# Group A: whole-word patterns matched with \b boundaries.
_BLOCKED_WORDS = [
    "curl",
    "wget",
    "nc",
    "netcat",
    "telnet",
    "ssh",
    "scp",
    "ftp",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "mkfs",
    "eval",
    "exec",
]

# Group B: multi-word/substring patterns matched literally.
_BLOCKED_PHRASES = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf .",
    "dd if=",
    "> /dev/sd",
    "chmod 777 /",
    "chown -R /",
    ":(){ :|:& };:",  # fork bomb
    "/etc/passwd",
    "/etc/shadow",
]


def _resolve_base(cmd_part: str) -> str:
    """Extract the base command from a single command part (no pipes)."""
    cmd_part = cmd_part.strip()
    try:
        parts = shlex.split(cmd_part)
    except ValueError:
        return ""
    if not parts:
        return ""
    return parts[0]


def _split_pipe_parts(cmd: str) -> list[str]:
    """Split a command string by pipe symbols, respecting shell quoting.

    Does not split on | inside single or double quotes.
    Does not treat || (shell OR) as a pipe.
    """
    parts = []
    current = []
    in_single = False
    in_double = False
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if in_single:
            current.append(ch)
            if ch == "'":
                in_single = False
        elif in_double:
            current.append(ch)
            if ch == '"':
                in_double = False
        elif ch == "'":
            current.append(ch)
            in_single = True
        elif ch == '"':
            current.append(ch)
            in_double = True
        elif ch == "|" and i + 1 < len(cmd) and cmd[i + 1] == "|":
            # || is shell OR, not a pipe — treat as literal
            current.append("||")
            i += 1
        elif ch == "|":
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current).strip())
    return parts


def _validate_command(cmd: str, allow_dangerous: bool = False) -> tuple[bool, str]:
    """Validate a command against safety rules.

    Returns (is_safe, reason).

    For piped commands, each pipe part is validated individually.
    Pipe splitting respects shell quoting — | inside quotes is not a separator.
    """
    cmd_lower = cmd.lower().strip()

    # Check blocked word patterns (whole-word matching)
    for word in _BLOCKED_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", cmd_lower):
            if allow_dangerous:
                logger.warning("DANGEROUS command allowed via flag: %s", cmd)
                return True, ""
            return False, f"blocked pattern: '{word}'"

    # Check blocked phrase patterns (literal substring matching)
    for phrase in _BLOCKED_PHRASES:
        if phrase in cmd_lower:
            if allow_dangerous:
                logger.warning("DANGEROUS command allowed via flag: %s", cmd)
                return True, ""
            return False, f"blocked pattern: '{phrase}'"

    # For piped commands, validate each pipe part separately
    # Use quote-aware pipe splitting
    if _PIPE_SEP in cmd:
        # Quick check: if all | are inside quotes, treat as no pipe
        pipe_parts = _split_pipe_parts(cmd)
        if len(pipe_parts) > 1:
            for part in pipe_parts:
                base = _resolve_base(part)
                if base and base not in _ALLOWED_COMMANDS:
                    if allow_dangerous:
                        logger.warning("Unknown command in pipe allowed via flag: %s", cmd)
                        return True, ""
                    return False, f"command in pipe not in allowlist: '{base}'"
            return True, ""

    # For non-piped commands without shell metacharacters, check against allowlist
    base = _resolve_base(cmd)
    if base and not _SHELL_CHARS.intersection(cmd) and base not in _ALLOWED_COMMANDS:
        if allow_dangerous:
            logger.warning("Unknown command allowed via flag: %s", cmd)
            return True, ""
        return False, f"command not in allowlist: '{base}'"

    return True, ""


def _is_safe_command(cmd: str) -> bool:
    """Check if a command is considered safe (no shell metacharacters, in allowlist)."""
    if _SHELL_CHARS.intersection(cmd):
        return False
    base = _resolve_base(cmd)
    return base in _ALLOWED_COMMANDS if base else False


def _get_audit_log_path() -> Path | None:
    """Get path for audit log file."""
    try:
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            cfg = parent / ".arachna.json"
            if cfg.exists():
                try:
                    config = json.loads(cfg.read_text())
                    out_dir = config.get("output_dir", "arachna_context")
                    return parent / out_dir / ".arachna_commands.log"
                except (json.JSONDecodeError, OSError):
                    pass
        return cwd / "arachna_context" / ".arachna_commands.log"
    except Exception:
        return None


def _log_command(cmd: str, success: bool):
    """Write command execution to audit log."""
    log_path = _get_audit_log_path()
    if log_path is None:
        return
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        from datetime import datetime

        timestamp = datetime.now().isoformat()
        status = "OK" if success else "FAIL"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {status}: {cmd}\n")
    except OSError:
        pass


def run_command(
    cmd: str,
    allow_dangerous: bool = False,
    interactive: bool = False,
    dry_run: bool = False,
) -> str:
    """Run shell command and return stdout.

    Uses shlex.split() for simple commands (no shell injection).
    Uses shell=True for commands with shell metacharacters (|, ||, &&, etc).

    Commands are validated against safety rules before execution.
    Blocked commands trigger a prompt in interactive mode, or are silently
    rejected in non-interactive mode.

    In dry_run mode, unsafe commands are shown but not executed.
    Safe commands (in allowlist, no shell metacharacters) are still executed
    in dry_run mode — they're considered safe for preview.
    """
    if not cmd.strip():
        return ""

    is_safe, reason = _validate_command(cmd, allow_dangerous)

    if not is_safe:
        logger.warning("Blocked command: %s — %s", cmd, reason)
        if interactive and sys.stdin.isatty():
            print("\n⚠  Potentially dangerous command blocked:")
            print(f"   {cmd}")
            print(f"   Reason: {reason}")
            response = input("   Execute anyway? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                _log_command(cmd, False)
                return ""
        else:
            _log_command(cmd, False)
            return ""

    # Dry-run mode: show what would be executed, skip if unsafe
    if dry_run:
        if _is_safe_command(cmd):
            # Safe commands are executed even in dry-run (e.g., echo for testing)
            pass
        else:
            print(f"  [DRY-RUN] Would execute: {cmd}")
            if interactive and sys.stdin.isatty():
                print("\n⚠  Command requires shell or is not in allowlist:")
                print(f"   {cmd}")
                response = input("   Execute anyway? [y/N]: ").strip().lower()
                if response not in ("y", "yes"):
                    _log_command(cmd, False)
                    return ""
            else:
                _log_command(cmd, False)
                return ""

    needs_shell = any(c in cmd for c in _SHELL_CHARS)

    try:
        if needs_shell:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        else:
            try:
                args = shlex.split(cmd)
            except ValueError as e:
                logger.warning("Invalid shell syntax in command: %s — %s", cmd, e)
                _log_command(cmd, False)
                return ""
            if not args:
                logger.warning("Empty command after parsing: %s", cmd)
                _log_command(cmd, False)
                return ""
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        _log_command(cmd, True)
        return result.stdout
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError, ValueError):
        _log_command(cmd, False)
        return ""
