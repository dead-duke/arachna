"""Safe command execution with sandbox validation and audit logging."""

import logging
import shlex
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("arachna.runner")

# Shell metacharacters that require shell=True
_SHELL_CHARS = {"|", "&", ";", "<", ">", "$", "`", "(", ")", "{", "}"}

# Safe utilities that don't download/execute external code
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
        "sed",
        "awk",
        "xargs",
        "tee",
        "git",
        "hg",
        "svn",
        "python",
        "python3",
        "node",
        "ruby",
        "perl",
        "php",
        "date",
        "env",
        "pwd",
        "whoami",
        "id",
        "uname",
        "which",
        "mkdir",
        "cp",
        "mv",
        "touch",
        "chmod",
        "chown",
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

# Dangerous commands/patterns blocked by default
_BLOCKED_PATTERNS = [
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
    "rm -rf /",
    "rm -rf ~",
    "rm -rf .",
    "mkfs",
    "dd if=",
    "> /dev/sd",
    "chmod 777 /",
    "chown -R /",
    ":(){ :|:& };:",  # fork bomb
    "eval",
    "exec",
    "/etc/passwd",
    "/etc/shadow",
]


def _resolve_command(cmd: str) -> str:
    """Extract the base command from a shell command string."""
    cmd = cmd.strip()
    if _SHELL_CHARS.intersection(cmd):
        return cmd
    parts = shlex.split(cmd)
    if not parts:
        return ""
    return parts[0]


def _validate_command(cmd: str, allow_dangerous: bool = False) -> tuple[bool, str]:
    """Validate a command against safety rules.

    Returns (is_safe, reason).
    """
    cmd_lower = cmd.lower().strip()

    for pattern in _BLOCKED_PATTERNS:
        if pattern in cmd_lower:
            if allow_dangerous:
                logger.warning("DANGEROUS command allowed via flag: %s", cmd)
                return True, ""
            return False, f"blocked pattern: '{pattern}'"

    base = _resolve_command(cmd)
    if base and not _SHELL_CHARS.intersection(cmd) and base not in _ALLOWED_COMMANDS:
        if allow_dangerous:
            logger.warning("Unknown command allowed via flag: %s", cmd)
            return True, ""
        return False, f"command not in allowlist: '{base}'"

    return True, ""


def _get_audit_log_path() -> Path | None:
    """Get path for audit log file."""
    try:
        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            cfg = parent / ".arachna.json"
            if cfg.exists():
                import json

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


def run_command(cmd: str, allow_dangerous: bool = False, interactive: bool = False) -> str:
    """Run shell command and return stdout.

    Uses shlex.split() for simple commands (no shell injection).
    Uses shell=True for commands with shell metacharacters (|, ||, &&, etc).

    Commands are validated against safety rules before execution.
    Blocked commands trigger a prompt in interactive mode, or are silently
    rejected in non-interactive mode.
    """
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

    needs_shell = any(c in cmd for c in _SHELL_CHARS)

    try:
        if needs_shell:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        else:
            args = shlex.split(cmd)
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        _log_command(cmd, True)
        return result.stdout
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError, ValueError):
        _log_command(cmd, False)
        return ""
