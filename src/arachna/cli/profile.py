# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna profile' command."""

import sys

from ..config import get_profile
from ..profiler import print_benchmark_table, run_benchmark
from . import register
from ._helpers import parse_output_dir


@register("profile")
def _cmd_benchmark(args, config: dict):
    profile_name = args.profile or "full"
    try:
        profile = get_profile(profile_name, config=config)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    output_dir = parse_output_dir(args, config)
    fmt = args.format or "terminal"

    print(f"Running benchmark on '{profile_name}' profile...")
    results = run_benchmark(profile, output_dir)
    print_benchmark_table(results, fmt)
