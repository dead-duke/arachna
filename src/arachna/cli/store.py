# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna store' command."""

import sys

from ..store import gc, stats
from . import register


@register("store-stats")
def _cmd_store_stats(args, config: dict):
    s = stats()
    print("Store statistics:")
    print(f"  Snapshots: {s['snapshots']}")
    print(f"  Objects: {s['objects']}")
    print(f"  Total size: {s['total_bytes']} bytes")
    print(f"  Unique content: {s['unique_bytes']} bytes ({s['dedup_pct']}% deduplication)")


@register("store-gc")
def _cmd_store_gc(args, config: dict):
    result = gc()
    if result["removed"] == 0:
        print("No objects to collect.")
    else:
        print(f"Removed {result['removed']} objects (freed {result['freed_bytes']} bytes).")


def _dispatch_store(args, config: dict, parser):
    store_cmd = getattr(args, "store_command", None)
    if store_cmd == "stats":
        _cmd_store_stats(args, config)
    elif store_cmd == "gc":
        _cmd_store_gc(args, config)
    else:
        store_p = None
        for action in parser._actions:
            if action.dest == "command" and hasattr(action, "choices"):
                choices = action.choices
                if "store" in choices:
                    store_p = choices["store"]
                    break
        if store_p:
            store_p.print_help()
        sys.exit(1)
