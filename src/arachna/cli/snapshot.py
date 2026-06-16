# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna snapshot' command.

v4.0.1: _dispatch_snapshot uses dict mapping instead of if/elif chain.
"""

import sys

from ..config.config import get_profile
from ..watch.store import delete_snapshot, list_snapshots, validate_snapshot_id
from ..watch.store_errors import SnapshotExistsError
from ..watch.watcher import create_snapshot as watch_create_snapshot
from ..watch.watcher import update_snapshot as watch_update_snapshot
from . import register
from ._helpers import format_profile_section, get_root


@register("snapshot-create")
def _cmd_snapshot_create(args, config: dict):
    if not args.name:
        print("Error: --name is required for 'create'.")
        sys.exit(1)
    try:
        validate_snapshot_id(args.name)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    root = get_root(config)
    profile_name = args.profile or "full"
    try:
        profile = get_profile(profile_name, root=root, config=config)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        sid = watch_create_snapshot(profile, name=args.name, root=root)
        print(f"Snapshot '{sid}' created.")
    except SnapshotExistsError as e:
        print(f"Error: {e}")
        sys.exit(1)


@register("snapshot-list")
def _cmd_snapshot_list(args, config: dict):
    root = get_root(config)
    snaps = list_snapshots(root=root)
    if not snaps:
        print("No snapshots found.")
        return
    print("Snapshots:")
    for s in snaps:
        created = s.get("created", "?")
        file_count = len(s.get("files", {}))
        print(f"  {s['id']:30} {created:25} {file_count} files")


@register("snapshot-update")
def _cmd_snapshot_update(args, config: dict):
    sid = args.id
    try:
        validate_snapshot_id(sid)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    root = get_root(config)
    profile = None
    if args.profile:
        try:
            profile = get_profile(args.profile, root=root, config=config)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)

    try:
        watch_update_snapshot(sid, root=root, profile=profile)
        print(f"Snapshot '{sid}' updated.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@register("snapshot-delete")
def _cmd_snapshot_delete(args, config: dict):
    sid = args.id
    try:
        validate_snapshot_id(sid)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    root = get_root(config)
    try:
        delete_snapshot(sid, root=root)
        print(f"Snapshot '{sid}' deleted.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@register("snapshot-info")
def _cmd_snapshot_info(args, config: dict):
    sid = args.id
    try:
        validate_snapshot_id(sid)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    root = get_root(config)
    try:
        all_manifests = list_snapshots(root=root)
        target = None
        for m in all_manifests:
            if m["id"] == sid:
                target = m
                break
        if target is None:
            print(f"Error: Snapshot '{sid}' not found.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.profile_only:
        prof = target.get("profile", {})
        if isinstance(prof, dict):
            print("Profile:")
            print(format_profile_section(prof))
        else:
            print(f"Profile: {prof} (legacy format)")
        return

    if args.stats_only:
        file_count = len(target.get("files", {}))
        pre_count = len(target.get("pre_commands", {}))
        cmd_count = len(target.get("command", {}))
        print(f"Files: {file_count}")
        print(f"Pre-commands: {pre_count}")
        print(f"Command: {cmd_count}")
        return

    print(f"Snapshot: {target['id']}")
    print(f"Created: {target.get('created', '?')}")
    file_count = len(target.get("files", {}))
    pre_count = len(target.get("pre_commands", {}))
    cmd = target.get("command", {})
    print(f"Files: {file_count}")
    print(f"Pre-commands: {pre_count}")
    print(f"Command: {'none' if not cmd else list(cmd.keys())}")
    print()
    prof = target.get("profile", {})
    if isinstance(prof, dict):
        print("Profile:")
        print(format_profile_section(prof))
    else:
        print(f"Profile: {prof} (legacy format)")


@register("snapshot-rename")
def _cmd_snapshot_rename(args, config: dict):
    from ..watch.store import rename_snapshot as store_rename_snapshot

    try:
        validate_snapshot_id(args.old)
        validate_snapshot_id(args.new)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    root = get_root(config)
    try:
        store_rename_snapshot(args.old, args.new, root=root)
        print(f"Snapshot '{args.old}' renamed to '{args.new}'.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


_SNAPSHOT_HANDLERS = {
    "create": _cmd_snapshot_create,
    "list": _cmd_snapshot_list,
    "update": _cmd_snapshot_update,
    "delete": _cmd_snapshot_delete,
    "info": _cmd_snapshot_info,
    "rename": _cmd_snapshot_rename,
}


def _dispatch_snapshot(args, config: dict, parser):
    snap_cmd = getattr(args, "snap_command", None)
    handler = _SNAPSHOT_HANDLERS.get(snap_cmd)
    if handler:
        handler(args, config)
    else:
        snap_p = None
        for action in parser._actions:
            if action.dest == "command" and hasattr(action, "choices"):
                choices = action.choices
                if "snapshot" in choices:
                    snap_p = choices["snapshot"]
                    break
        if snap_p:
            snap_p.print_help()
        sys.exit(1)
