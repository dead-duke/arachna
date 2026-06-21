"""CLI handlers for 'arachna snapshot' command."""

import sys

from ..config.core.config import get_profile
from ..config.profile_config import ArachnaConfig
from ..snapshot.diff.snapshot_diff import create_snapshot as snap_create_snapshot
from ..snapshot.diff.snapshot_diff import update_snapshot as snap_update_snapshot
from ..snapshot.store.store import delete_snapshot, list_snapshots, validate_snapshot_id
from ..snapshot.store.store_errors import SnapshotExistsError
from . import register
from ._helpers import format_profile_section, get_root


@register("snapshot-create")
def _cmd_snapshot_create(args, config: ArachnaConfig | dict):
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
        profile = get_profile(
            profile_name, root=root, config=config if isinstance(config, ArachnaConfig) else None
        )
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)
    try:
        sid = snap_create_snapshot(profile, name=args.name, root=root)
        print(f"Snapshot '{sid}' created.")
    except SnapshotExistsError as e:
        print(f"Error: {e}")
        sys.exit(1)


@register("snapshot-list")
def _cmd_snapshot_list(args, config: ArachnaConfig | dict):
    root = get_root(config)
    snaps = list_snapshots(root=root)
    if not snaps:
        print("No snapshots found.")
        return
    print("Snapshots:")
    for s in snaps:
        print(f"  {s['id']:30} {s.get('created', '?'):25} {len(s.get('files', {}))} files")


@register("snapshot-update")
def _cmd_snapshot_update(args, config: ArachnaConfig | dict):
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
            profile = get_profile(
                args.profile,
                root=root,
                config=config if isinstance(config, ArachnaConfig) else None,
            )
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)
    try:
        snap_update_snapshot(sid, root=root, profile=profile)
        print(f"Snapshot '{sid}' updated.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


@register("snapshot-delete")
def _cmd_snapshot_delete(args, config: ArachnaConfig | dict):
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


def _print_snapshot_details(target, args):
    if args.profile_only:
        prof = target.get("profile", {})
        if isinstance(prof, dict):
            print("Profile:")
            print(format_profile_section(prof))
        else:
            print(f"Profile: {prof} (legacy format)")
        return
    if args.stats_only:
        print(f"Files: {len(target.get('files', {}))}")
        print(f"Pre-commands: {len(target.get('pre_commands', {}))}")
        print(f"Command: {len(target.get('command', {}))}")
        return
    print(f"Snapshot: {target['id']}")
    print(f"Created: {target.get('created', '?')}")
    print(f"Files: {len(target.get('files', {}))}")
    print(f"Pre-commands: {len(target.get('pre_commands', {}))}")
    cmd = target.get("command", {})
    print(f"Command: {'none' if not cmd else list(cmd.keys())}")
    print()
    prof = target.get("profile", {})
    if isinstance(prof, dict):
        print("Profile:")
        print(format_profile_section(prof))
    else:
        print(f"Profile: {prof} (legacy format)")


@register("snapshot-info")
def _cmd_snapshot_info(args, config: ArachnaConfig | dict):
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
    _print_snapshot_details(target, args)


@register("snapshot-rename")
def _cmd_snapshot_rename(args, config: ArachnaConfig | dict):
    from ..snapshot.store.store import rename_snapshot as store_rename_snapshot

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


def _dispatch_snapshot(args, config: ArachnaConfig | dict, parser):
    snap_cmd = getattr(args, "snap_command", None)
    handler = _SNAPSHOT_HANDLERS.get(snap_cmd)
    if handler:
        handler(args, config)
    else:
        snap_p = None
        for action in parser._actions:
            if (
                action.dest == "command"
                and hasattr(action, "choices")
                and "snapshot" in action.choices
            ):
                snap_p = action.choices["snapshot"]
                break
        if snap_p:
            snap_p.print_help()
        sys.exit(1)
