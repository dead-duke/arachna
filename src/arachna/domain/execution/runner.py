# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Safe command execution with sandbox validation and audit logging."""

import json
import logging
import os as _os
import re
import shlex
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("arachna.runner")

_SHELL_CHARS = {"|", "&", ";", "<", ">", "$", "`", "(", ")", "{", "}"}
_PIPE_SEP = "|"
_RESTRICTED_COMMANDS = frozenset(
    {"echo", "date", "pwd", "whoami", "id", "uname", "which", "true", "false", "test", "["}
)
_ALLOWED_COMMANDS = _RESTRICTED_COMMANDS | {
    "cat",
    "ls",
    "tree",
    "grep",
    "wc",
    "sort",
    "uniq",
    "head",
    "tail",
    "cut",
    "tr",
    "git",
    "diff",
    "comm",
    "join",
    "paste",
}
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
    "find",
]
_BLOCKED_PHRASES = [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf .",
    "dd if=",
    "> /dev/sd",
    "chmod 777 /",
    "chown -R /",
    ":(){ :|:& };:",
    "/etc/passwd",
    "/etc/shadow",
]


def _sanitize_log(text: str) -> str:
    """Escape newlines and carriage returns for safe log output."""
    return text.replace("\n", "\\n").replace("\r", "\\r")


def _resolve_base(cmd_part: str) -> str:
    cmd_part = cmd_part.strip()
    try:
        parts = shlex.split(cmd_part)
    except ValueError:
        return ""
    return parts[0] if parts else ""


def _process_escape(cmd, i, current):
    if i + 1 >= len(cmd):
        current.append("\\")
        return "normal", i
    next_ch = cmd[i + 1]
    if next_ch == "|":
        current.append("|")
    elif next_ch == "\\":
        current.append("\\")
    else:
        current.append("\\")
    return "normal", i + 1


def _process_normal_char(cmd, i, current, parts):
    ch = cmd[i]
    if ch == "\\" and i + 1 < len(cmd):
        return _process_escape(cmd, i, current)
    elif ch == "'":
        current.append(ch)
        return "single", i
    elif ch == '"':
        current.append(ch)
        return "double", i
    elif ch == "|" and i + 1 < len(cmd) and cmd[i + 1] == "|":
        current.append("||")
        return "normal", i + 1
    elif ch == "|":
        parts.append("".join(current).strip())
        current.clear()
        return "normal", i
    else:
        current.append(ch)
        return "normal", i


def _process_single_quote(cmd, i, current):
    current.append(cmd[i])
    return ("normal", i) if cmd[i] == "'" else ("single", i)


def _process_double_quote(cmd, i, current):
    ch = cmd[i]
    if ch == "\\" and i + 1 < len(cmd):
        next_ch = cmd[i + 1]
        if next_ch in ("$", "`", '"', "\\", "\n"):
            current.append("\\")
            current.append(next_ch)
            return "double", i + 1
        else:
            current.append("\\")
            return "double", i
    else:
        current.append(ch)
        return ("normal", i) if ch == '"' else ("double", i)


def _split_pipe_parts(cmd: str) -> list[str]:
    parts = []
    current = []
    state = "normal"
    i = 0
    while i < len(cmd):
        if state == "normal":
            state, i = _process_normal_char(cmd, i, current, parts)
        elif state == "single":
            state, i = _process_single_quote(cmd, i, current)
        elif state == "double":
            state, i = _process_double_quote(cmd, i, current)
        i += 1
    parts.append("".join(current).strip())
    return parts


def _check_blocked_words(cmd_lower):
    return next(
        (
            (False, f"blocked pattern: '{w}'")
            for w in _BLOCKED_WORDS
            if re.search(r"\b" + re.escape(w) + r"\b", cmd_lower)
        ),
        (True, ""),
    )


def _check_blocked_phrases(cmd_lower):
    return next(
        ((False, f"blocked pattern: '{p}'") for p in _BLOCKED_PHRASES if p in cmd_lower),
        (True, ""),
    )


def _check_shell_metachars(cmd, allow_file_args):
    if not allow_file_args and _SHELL_CHARS.intersection(cmd):
        return False, "shell metacharacters not allowed in restricted mode"
    if "$(" in cmd or "`" in cmd:
        return False, "command substitution not allowed"
    return True, ""


def _check_pipe_parts(cmd, allowlist):
    return next(
        (
            (False, f"command in pipe not in allowlist: '{_resolve_base(p)}'")
            for p in _split_pipe_parts(cmd)
            if _PIPE_SEP in cmd
            and len(_split_pipe_parts(cmd)) > 1
            and _resolve_base(p)
            and _resolve_base(p) not in allowlist
        ),
        (True, ""),
    )


def _check_base_command(cmd, allowlist):
    if _SHELL_CHARS.intersection(cmd):
        return True, ""
    base = _resolve_base(cmd)
    if base and base not in allowlist:
        return False, f"command not in allowlist: '{base}'"
    return True, ""


def _handle_dangerous_override(is_safe, reason, allow_dangerous, cmd):
    if not is_safe and allow_dangerous:
        safe_cmd = _sanitize_log(cmd)
        logger.error("DANGEROUS command allowed via flag: %s", safe_cmd)
        return True, ""
    return is_safe, reason


def _validate_command(
    cmd: str, allow_dangerous: bool = False, allow_file_args: bool = False
) -> tuple[bool, str]:
    cmd_lower = cmd.lower().strip()
    allowlist = _ALLOWED_COMMANDS if allow_file_args else _RESTRICTED_COMMANDS
    for is_safe, reason in [
        _check_blocked_words(cmd_lower),
        _check_blocked_phrases(cmd_lower),
        _check_shell_metachars(cmd, allow_file_args),
        _check_pipe_parts(cmd, allowlist),
        _check_base_command(cmd, allowlist),
    ]:
        is_safe, reason = _handle_dangerous_override(is_safe, reason, allow_dangerous, cmd)
        if not is_safe:
            return False, reason
    return True, ""


def _is_safe_command(cmd, allow_file_args=False):
    if _SHELL_CHARS.intersection(cmd):
        return False
    base = _resolve_base(cmd)
    if not base:
        return False
    allowlist = _ALLOWED_COMMANDS if allow_file_args else _RESTRICTED_COMMANDS
    return base in allowlist


def _get_audit_log_path(root: Path) -> Path | None:
    try:
        for i, parent in enumerate([root, *root.parents]):
            if i > 5:
                break
            cfg = parent / ".arachna.json"
            if cfg.exists():
                try:
                    config = json.loads(cfg.read_text())
                    return (
                        parent
                        / config.get("output_dir", "arachna_context")
                        / ".arachna_commands.log"
                    )
                except (json.JSONDecodeError, OSError):
                    pass
        return root / "arachna_context" / ".arachna_commands.log"
    except OSError:
        return None


def _write_log(log_path, entry, log_writer=None):
    if log_writer is not None:
        log_writer(log_path, entry)
        return
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass


def _log_command(cmd, success, root, log_writer=None):
    log_path = _get_audit_log_path(root)
    if log_path is None:
        return
    status = "OK" if success else "FAIL"
    sanitized_cmd = _sanitize_log(cmd)
    _write_log(
        log_path,
        f"[{datetime.now().isoformat()}] {status}: {sanitized_cmd}\n",
        log_writer=log_writer,
    )


def _run_popen(cmd, needs_shell, max_output_size):
    try:
        if needs_shell:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,  # nosec B602 — pre_commands with pipes/shell features, protected by allowlist
                text=True,
            )
        else:
            process = subprocess.Popen(
                shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
        output_parts = []
        total_size = 0
        while True:
            chunk = process.stdout.read(65536)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_output_size:
                process.kill()
                process.wait()
                keep = max_output_size - (total_size - len(chunk))
                return (
                    "".join(output_parts)
                    + chunk[:keep]
                    + "\n\n# ... output truncated (exceeds size limit) ...\n",
                    True,
                )
            output_parts.append(chunk)
        process.wait()
        return "".join(output_parts), False
    except (OSError, ValueError):
        return "", False


def _execute_command(cmd, root, max_output_size, log_writer=None):
    output, was_truncated = _run_popen(cmd, any(c in cmd for c in _SHELL_CHARS), max_output_size)
    if was_truncated:
        logger.warning("Command output truncated: %s", cmd[:80])
    _log_command(cmd, True, root, log_writer=log_writer)
    return output


def _handle_interactive_blocked(cmd, reason, root, max_output_size, log_writer=None):
    print("\n⚠  Potentially dangerous command blocked:")
    print(f"   {cmd}")
    print(f"   Reason: {reason}")
    if input("   Execute anyway? [y/N]: ").strip().lower() in ("y", "yes"):
        return _execute_command(cmd, root, max_output_size, log_writer=log_writer)
    _log_command(cmd, False, root, log_writer=log_writer)
    return ""


def _handle_dry_run_unsafe(cmd, root, max_output_size, log_writer=None):
    print(f"  [DRY-RUN] Would execute: {cmd}")
    if sys.stdin.isatty():
        print("\n⚠  Command requires shell or is not in allowlist:")
        print(f"   {cmd}")
        if input("   Execute anyway? [y/N]: ").strip().lower() in ("y", "yes"):
            return _execute_command(cmd, root, max_output_size, log_writer=log_writer)
    _log_command(cmd, False, root, log_writer=log_writer)
    return ""


def run_command(
    cmd,
    root,
    allow_dangerous=False,
    interactive=False,
    dry_run=False,
    allow_file_args=False,
    max_output_size=None,
    log_writer: Callable[[Path, str], None] | None = None,
):
    if not cmd.strip():
        return ""
    if max_output_size is None:
        max_output_size = int(_os.environ.get("ARACHNA_MAX_OUTPUT_SIZE", "10485760"))
    is_safe, reason = _validate_command(cmd, allow_dangerous, allow_file_args=allow_file_args)
    if not is_safe:
        if interactive and sys.stdin.isatty():
            return _handle_interactive_blocked(
                cmd, reason, root, max_output_size, log_writer=log_writer
            )
        _log_command(cmd, False, root, log_writer=log_writer)
        return ""
    if dry_run and not _is_safe_command(cmd, allow_file_args=allow_file_args):
        return _handle_dry_run_unsafe(cmd, root, max_output_size, log_writer=log_writer)
    return _execute_command(cmd, root, max_output_size, log_writer=log_writer)


def run_pre_commands(commands, root, pre_command_delay=None):
    if pre_command_delay is None:
        pre_command_delay = float(_os.environ.get("ARACHNA_PRE_COMMAND_DELAY", "0"))
    results = []
    for i, cmd in enumerate(commands):
        if i > 0 and pre_command_delay > 0:
            time.sleep(pre_command_delay)
        try:
            results.append((cmd, run_command(cmd, root=root, allow_file_args=True)))
        except OSError as e:
            logger.warning("pre_command failed: %s - %s", cmd[:80], e)
            results.append((cmd, ""))
    return results
