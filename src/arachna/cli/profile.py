"""CLI handlers for 'arachna profile' command."""

import sys
from pathlib import Path

from ..config.core.config import get_profile
from ..config.profile_config import ArachnaConfig
from ..config.profiler import print_benchmark_table, run_benchmark
from ..snapshot.benchmarks import benchmark_plugins
from . import register
from ._helpers import parse_output_dir


@register("profile")
def _cmd_benchmark(args, config: ArachnaConfig | dict):
    profile_name = args.profile or "full"
    if isinstance(config, ArachnaConfig):
        root = Path(config._root or Path.cwd())
    else:
        root = Path(config.get("_root", Path.cwd()))
    try:
        profile = get_profile(profile_name, root=root)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    output_dir = parse_output_dir(args, config)
    fmt = args.format or "terminal"

    print(f"Running benchmark on '{profile_name}' profile...")
    results = run_benchmark(profile, output_dir, root=root)
    plugin_results = benchmark_plugins(profile, output_dir, root=root)
    if plugin_results:
        results.update(plugin_results)
    print_benchmark_table(results, fmt)
