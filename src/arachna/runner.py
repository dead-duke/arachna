"""Safe command execution."""

import shlex
import subprocess

# Shell metacharacters that require shell=True
_SHELL_CHARS = {"|", "&", ";", "<", ">", "$", "`", "(", ")", "{", "}"}


def run_command(cmd: str) -> str:
    """Run shell command and return stdout.

    Uses shlex.split() for simple commands (no shell injection).
    Uses shell=True for commands with shell metacharacters (|, ||, &&, etc).
    """
    needs_shell = any(c in cmd for c in _SHELL_CHARS)

    try:
        if needs_shell:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
        else:
            args = shlex.split(cmd)
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=30
            )
        return result.stdout
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError, ValueError):
        return ""
