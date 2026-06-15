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


def _resolve_base(cmd_part: str) -> str:
    cmd_part = cmd_part.strip()
    try:
        parts = shlex.split(cmd_part)
    except ValueError:
        return ""
    return parts[0] if parts else ""


def _split_pipe_parts(cmd: str) -> list[str]:
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
            if ch == "\\" and i + 1 < len(cmd):
                next_ch = cmd[i + 1]
                if next_ch in ("$", "`", '"', "\\", "\n"):
                    current.append("\\")
                    current.append(next_ch)
                    i += 1
                else:
                    current.append("\\")
            else:
                current.append(ch)
                if ch == '"':
                    in_double = False
        elif ch == "\\" and i + 1 < len(cmd):
            next_ch = cmd[i + 1]
            if next_ch == "|":
                current.append("|")
                i += 1
            elif next_ch == "\\":
                current.append("\\")
                i += 1
            else:
                current.append("\\")
        elif ch == "'":
            current.append(ch)
            in_single = True
        elif ch == '"':
            current.append(ch)
            in_double = True
        elif ch == "|" and i + 1 < len(cmd) and cmd[i + 1] == "|":
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


def _validate_command(
    cmd: str, allow_dangerous: bool = False, allow_file_args: bool = False
) -> tuple[bool, str]:
    cmd_lower = cmd.lower().strip()
    allowlist = _ALLOWED_COMMANDS if allow_file_args else _RESTRICTED_COMMANDS

    for word in _BLOCKED_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", cmd_lower):
            if allow_dangerous:
                logger.warning("DANGEROUS command allowed via flag: %s", cmd)
                return True, ""
            return False, f"blocked pattern: '{word}'"

    for phrase in _BLOCKED_PHRASES:
        if phrase in cmd_lower:
            if allow_dangerous:
                logger.warning("DANGEROUS command allowed via flag: %s", cmd)
                return True, ""
            return False, f"blocked pattern: '{phrase}'"

    if not allow_file_args and _SHELL_CHARS.intersection(cmd):
        if allow_dangerous:
            logger.warning("Shell metacharacters allowed via flag: %s", cmd)
            return True, ""
        return False, "shell metacharacters not allowed in restricted mode"

    if _PIPE_SEP in cmd:
        pipe_parts = _split_pipe_parts(cmd)
        if len(pipe_parts) > 1:
            for part in pipe_parts:
                base = _resolve_base(part)
                if base and base not in allowlist:
                    if allow_dangerous:
                        logger.warning("Unknown command in pipe allowed via flag: %s", cmd)
                        return True, ""
                    return False, f"command in pipe not in allowlist: '{base}'"
            return True, ""

    if not _SHELL_CHARS.intersection(cmd):
        base = _resolve_base(cmd)
        if base and base not in allowlist:
            if allow_dangerous:
                logger.warning("Unknown command allowed via flag: %s", cmd)
                return True, ""
            return False, f"command not in allowlist: '{base}'"

    return True, ""


def _is_safe_command(cmd: str, allow_file_args: bool = False) -> bool:
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
                    out_dir = config.get("output_dir", "arachna_context")
                    return parent / out_dir / ".arachna_commands.log"
                except (json.JSONDecodeError, OSError):
                    pass
        return root / "arachna_context" / ".arachna_commands.log"
    except Exception:
        return None


_log_writer = None


def _write_log(log_path: Path, entry: str):
    if _log_writer is not None:
        _log_writer(log_path, entry)
        return
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass


def _log_command(cmd: str, success: bool, root: Path):
    log_path = _get_audit_log_path(root)
    if log_path is None:
        return
    from datetime import datetime

    timestamp = datetime.now().isoformat()
    status = "OK" if success else "FAIL"
    sanitized_cmd = cmd.replace("\n", "\\n").replace("\r", "\\r")
    _write_log(log_path, f"[{timestamp}] {status}: {sanitized_cmd}\n")


def _run_popen(cmd: str, needs_shell: bool, max_output_size: int) -> tuple[str, bool]:
    try:
        if needs_shell:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, text=True
            )
        else:
            args = shlex.split(cmd)
            process = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
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
                truncated = "\n\n# ... output truncated (exceeds size limit) ...\n"
                output_parts.append(chunk[:keep] + truncated)
                return "".join(output_parts), True
            output_parts.append(chunk)

        process.wait()
        return "".join(output_parts), False
    except (OSError, FileNotFoundError, ValueError):
        return "", False


def run_command(
    cmd: str,
    root: Path,
    allow_dangerous: bool = False,
    interactive: bool = False,
    dry_run: bool = False,
    allow_file_args: bool = False,
    max_output_size: int | None = None,
) -> str:
    if not cmd.strip():
        return ""

    if max_output_size is None:
        max_output_size = int(_os.environ.get("ARACHNA_MAX_OUTPUT_SIZE", "10485760"))

    is_safe, reason = _validate_command(cmd, allow_dangerous, allow_file_args=allow_file_args)

    if not is_safe:
        logger.warning("Blocked command: %s - %s", cmd, reason)
        if interactive and sys.stdin.isatty():
            print("\n⚠  Potentially dangerous command blocked:")
            print(f"   {cmd}")
            print(f"   Reason: {reason}")
            response = input("   Execute anyway? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                _log_command(cmd, False, root)
                return ""
        else:
            _log_command(cmd, False, root)
            return ""

    if dry_run:
        if _is_safe_command(cmd, allow_file_args=allow_file_args):
            pass
        else:
            print(f"  [DRY-RUN] Would execute: {cmd}")
            if interactive and sys.stdin.isatty():
                print("\n⚠  Command requires shell or is not in allowlist:")
                print(f"   {cmd}")
                response = input("   Execute anyway? [y/N]: ").strip().lower()
                if response not in ("y", "yes"):
                    _log_command(cmd, False, root)
                    return ""
            else:
                _log_command(cmd, False, root)
                return ""

    needs_shell = any(c in cmd for c in _SHELL_CHARS)
    output, was_truncated = _run_popen(cmd, needs_shell, max_output_size)
    if was_truncated:
        logger.warning("Command output truncated: %s", cmd[:80])
    _log_command(cmd, True, root)
    return output


def run_pre_commands(
    commands: list[str],
    root: Path,
    pre_command_delay: float | None = None,
) -> list[tuple[str, str]]:
    if pre_command_delay is None:
        pre_command_delay = float(_os.environ.get("ARACHNA_PRE_COMMAND_DELAY", "0"))

    results = []
    for i, cmd in enumerate(commands):
        if i > 0 and pre_command_delay > 0:
            time.sleep(pre_command_delay)
        try:
            output = run_command(cmd, root=root, allow_file_args=True)
            results.append((cmd, output))
        except Exception as e:
            logger.warning("pre_command failed: %s - %s", cmd[:80], e)
            results.append((cmd, ""))
    return results
