# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI entry point for arachna v4.0.0 — argparse subparsers."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .cli import COMMAND_HANDLERS
from .config.config import find_config, load_config


def build_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="arachna — context collector for AI")
    parser.add_argument("--version", action="version", version=f"arachna v{__version__}")
    sub = parser.add_subparsers(dest="command")

    collect_p = sub.add_parser("collect", help="Collect project context")
    collect_p.add_argument("--profile", "-p", help="Profile name to collect")
    collect_p.add_argument("--all", "-a", action="store_true", help="Collect all profiles")
    collect_p.add_argument("--list", "-l", action="store_true", help="List available profiles")
    collect_p.add_argument("--validate", action="store_true", help="Validate config for errors")
    collect_p.add_argument("--clean", "-c", action="store_true", help="Remove all collected files")
    collect_p.add_argument("--dry-run", action="store_true")
    collect_p.add_argument("--output-dir", "-o", help="Override output directory")
    collect_p.add_argument("--verbose", "-v", action="store_true")
    collect_p.add_argument("--compress", action="store_true")
    collect_p.add_argument("--incremental", action="store_true")
    collect_p.add_argument("--format", choices=["markdown", "xml", "json"])
    collect_p.add_argument("--merge", action="store_true")
    collect_p.add_argument("--query", help="Filter files by query")
    collect_p.add_argument("--no-pre-commands", action="store_true")
    collect_p.add_argument("--mode", choices=["full", "headers", "repo-map"], default="full")

    manifest_p = sub.add_parser("manifest", help="Show collected files manifest")
    manifest_p.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    manifest_p.add_argument("--output-dir", "-o", help="Output directory")

    snap_p = sub.add_parser("snapshot", help="Manage snapshots")
    snap_subs = snap_p.add_subparsers(dest="snap_command")
    snap_create = snap_subs.add_parser("create", help="Create a named snapshot")
    snap_create.add_argument("--profile", "-p", help="Profile name (default: full)")
    snap_create.add_argument("--name", required=True, help="Snapshot name")
    snap_subs.add_parser("list", help="List all snapshots")
    snap_update = snap_subs.add_parser("update", help="Update an existing snapshot")
    snap_update.add_argument("id", help="Snapshot ID to update")
    snap_update.add_argument("--profile", "-p", help="Profile name (optional)")
    snap_delete = snap_subs.add_parser("delete", help="Delete a snapshot")
    snap_delete.add_argument("id", help="Snapshot ID to delete")
    snap_info = snap_subs.add_parser("info", help="Show snapshot details")
    snap_info.add_argument("id", help="Snapshot ID")
    snap_info.add_argument(
        "--profile", dest="profile_only", action="store_true", help="Profile only"
    )
    snap_info.add_argument("--stats", dest="stats_only", action="store_true", help="Stats only")
    snap_rename = snap_subs.add_parser("rename", help="Rename a snapshot")
    snap_rename.add_argument("old", help="Old snapshot ID")
    snap_rename.add_argument("new", help="New snapshot ID")

    diff_p = sub.add_parser("diff", help="Diff from snapshot")
    diff_p.add_argument("--from", dest="from_snapshot", help="Source snapshot ID")
    diff_p.add_argument("--to", help="Target snapshot ID (cross-snapshot)")
    diff_p.add_argument("--all", action="store_true", help="Full project as diff (no snapshot)")
    diff_p.add_argument("--profile", "-p", help="Profile name")
    diff_p.add_argument("--stat", action="store_true", help="Stats only, no files")
    diff_p.add_argument("--flat", action="store_true", help="Flat output (no grouping)")
    diff_p.add_argument("--format", choices=["markdown", "xml", "json"])
    diff_p.add_argument("--mode", choices=["full", "structural", "repo-map"])
    diff_p.add_argument("--compress", action="store_true")
    diff_p.add_argument("--output-dir", "-o", help="Output directory")
    diff_p.add_argument("--query", help="Filter files by query")

    store_p = sub.add_parser("store", help="Store management")
    store_subs = store_p.add_subparsers(dest="store_command")
    store_subs.add_parser("stats", help="Show store statistics")
    store_subs.add_parser("gc", help="Garbage collect store")

    plugins_p = sub.add_parser("plugins", help="Plugin management")
    plugins_subs = plugins_p.add_subparsers(dest="plugins_command")
    plugins_subs.add_parser("list", help="List plugins")
    plugins_install = plugins_subs.add_parser("install", help="Install plugin")
    plugins_install.add_argument(
        "language", help="Language to install (javascript, typescript, go, tiktoken)"
    )
    plugins_install.add_argument("--execute", action="store_true", help="Execute install command")
    plugins_uninstall = plugins_subs.add_parser("uninstall", help="Uninstall plugin")
    plugins_uninstall.add_argument("language", help="Language to uninstall")

    presets_p = sub.add_parser("presets", help="Preset management")
    presets_subs = presets_p.add_subparsers(dest="presets_command")
    presets_update = presets_subs.add_parser("update", help="Update presets from remote")
    presets_update.add_argument("--url", help="Remote presets URL")

    bench_p = sub.add_parser("profile", help="Profile project — measure token savings across modes")
    bench_p.add_argument("--profile", "-p", help="Profile name (default: full)")
    bench_p.add_argument("--format", choices=["terminal", "json"], default="terminal")
    bench_p.add_argument("--output-dir", "-o", help="Output directory")

    sub.add_parser("doctor", help="Run configuration diagnostic")

    init_p = sub.add_parser("init", help="Create .arachna.json interactively")
    init_p.add_argument("--defaults", action="store_true", help="Use defaults (non-interactive)")
    init_p.add_argument("--preset", help="Use specific preset")
    init_p.add_argument("--install-hook", action="store_true", help="Install post-commit git hook")
    init_p.add_argument("--force", action="store_true")
    init_p.add_argument("--output-dir", "-o", help="Output directory")

    comp_p = sub.add_parser("completion", help="Generate shell completion")
    comp_p.add_argument("shell", nargs="?", choices=["bash", "zsh"], help="Shell: bash or zsh")

    return parser


def _dispatch_collect(args, config: dict):
    if args.list:
        return COMMAND_HANDLERS["collect-list"](args, config)
    if args.validate:
        return COMMAND_HANDLERS["collect-validate"](args, config)
    if args.clean:
        return COMMAND_HANDLERS["collect-clean"](args, config)
    if args.all:
        return COMMAND_HANDLERS["collect-all"](args, config)
    if args.profile:
        return COMMAND_HANDLERS["collect-profile"](args, config)
    print("Error: specify --profile, --all, --list, --validate, or --clean")
    sys.exit(1)


def main():
    parser = build_argparse()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    root = Path.cwd()
    cfg_path = find_config(root)
    config = load_config(root)
    if cfg_path is not None:
        config["_root"] = str(cfg_path.parent)

    if args.command == "collect":
        _dispatch_collect(args, config)

    elif args.command == "manifest":
        COMMAND_HANDLERS["manifest"](args, config)

    elif args.command == "snapshot":
        from .cli.snapshot import _dispatch_snapshot

        _dispatch_snapshot(args, config, parser)

    elif args.command == "diff":
        COMMAND_HANDLERS["diff"](args, config)

    elif args.command == "store":
        from .cli.store import _dispatch_store

        _dispatch_store(args, config, parser)

    elif args.command == "plugins":
        from .cli.plugins import _dispatch_plugins

        _dispatch_plugins(args, config, parser)

    elif args.command == "presets":
        COMMAND_HANDLERS["presets-update"](args, config)

    elif args.command == "profile":
        COMMAND_HANDLERS["profile"](args, config)

    elif args.command == "doctor":
        COMMAND_HANDLERS["doctor"](args, config)

    elif args.command == "init":
        from .cli.init import _dispatch_init

        _dispatch_init(args, config)

    elif args.command == "completion":
        COMMAND_HANDLERS["completion"](args, config)


if __name__ == "__main__":
    main()
