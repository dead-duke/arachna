# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna store' command.

v4.0.1: _dispatch_store uses dict mapping instead of if/elif chain.
"""

import sys

from ..watch.store import gc, stats
from . import register
from ._helpers import get_root


@register("store-stats")
def _cmd_store_stats(args, config: dict):
    root = get_root(config)
    s = stats(root=root)
    print("Store statistics:")
    print(f"  Snapshots: {s['snapshots']}")
    print(f"  Objects: {s['objects']}")
    print(f"  Total size: {s['total_bytes']} bytes")
    print(f"  Unique content: {s['unique_bytes']} bytes ({s['dedup_pct']}% deduplication)")


@register("store-gc")
def _cmd_store_gc(args, config: dict):
    root = get_root(config)
    result = gc(root=root)
    if result["removed"] == 0:
        print("No objects to collect.")
    else:
        print(f"Removed {result['removed']} objects (freed {result['freed_bytes']} bytes).")


_STORE_HANDLERS = {
    "stats": _cmd_store_stats,
    "gc": _cmd_store_gc,
}


def _dispatch_store(args, config: dict, parser):
    store_cmd = getattr(args, "store_command", None)
    handler = _STORE_HANDLERS.get(store_cmd)
    if handler:
        handler(args, config)
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
