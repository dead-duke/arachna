# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna init' command."""

import sys

from ..hook import install_hook
from . import register
from ._helpers import parse_output_dir


@register("init")
def _cmd_init(args, config: dict):
    from ..init import run_defaults, run_interactive

    output_dir = parse_output_dir(args, config)
    if args.defaults:
        run_defaults(output_dir, preset=args.preset)
    else:
        run_interactive(output_dir, preset=args.preset)


def _dispatch_init(args, config: dict):
    if args.install_hook:
        success, msg = install_hook(force=args.force)
        print(msg)
        sys.exit(0 if success else 1)
    else:
        _cmd_init(args, config)
