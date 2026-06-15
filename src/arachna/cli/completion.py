# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna completion' command."""

from ..config.completion import generate_bash, generate_zsh
from . import register


@register("completion")
def _cmd_completion(args, config: dict):
    shell = args.shell
    if shell == "bash":
        generate_bash()
    elif shell == "zsh":
        generate_zsh()
    else:
        print("Usage: arachna completion bash|zsh")
        print("  source <(arachna completion bash)")
        print("  source <(arachna completion zsh)")
