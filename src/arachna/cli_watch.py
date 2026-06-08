"""Watch CLI handlers — extracted from __main__.py.

Provides handle_watch_command(argv) -> bool entry point.
Returns True if argv is a Watch command and was handled.
"""

import sys
from pathlib import Path

from .collector import (
    _write_diff_parts,
    clean_manifest,
    collect,
    load_manifest,
    save_manifest,
)
from .config import get_profile, load_config
from .differ import compute_diff_stats
from .store import validate_snapshot_id
from .tokenizer import count_tokens, load_tokenizer


def handle_watch_command(argv: list[str]) -> bool:
    """Handle Watch commands from argv. Returns True if handled."""
    if "--snapshot" in argv:
        _cmd_snapshot(argv)
        return True
    if "--diff" in argv:
        _cmd_diff(argv)
        return True
    if "--store" in argv:
        _cmd_store(argv)
        return True
    return False


def _parse_output_dir(argv: list[str], config: dict) -> str:
    output_dir = config.get("output_dir", ".")
    if "--output-dir" in argv:
        idx = argv.index("--output-dir")
        if idx + 1 < len(argv):
            output_dir = argv[idx + 1]
    elif "-o" in argv:
        idx = argv.index("-o")
        if idx + 1 < len(argv):
            output_dir = argv[idx + 1]
    return output_dir


def _cmd_snapshot(argv: list[str]):
    from .store import delete_snapshot, list_snapshots
    from .store import rename_snapshot as store_rename_snapshot
    from .store_errors import SnapshotExistsError
    from .watcher import create_snapshot as watch_create_snapshot
    from .watcher import update_snapshot as watch_update_snapshot

    if "list" in argv:
        snaps = list_snapshots()
        if not snaps:
            print("No snapshots found.")
            return
        print("Snapshots:")
        for s in snaps:
            created = s.get("created", "?")
            file_count = len(s.get("files", {}))
            print(f"  {s['id']:30} {created:25} {file_count} files")
        return

    if "info" in argv:
        idx = argv.index("info")
        if idx + 1 >= len(argv):
            print("Usage: arachna --snapshot info <id> [--profile | --stats]")
            sys.exit(1)
        sid = argv[idx + 1]
        if sid.startswith("-"):
            print(f"Error: invalid snapshot ID '{sid}'")
            sys.exit(1)
        try:
            validate_snapshot_id(sid)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        try:
            all_manifests = list_snapshots()
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

        profile_only = "--profile" in argv
        stats_only = "--stats" in argv

        if profile_only:
            prof = target.get("profile", {})
            if isinstance(prof, dict):
                print("Profile:")
                for key, label in [
                    ("directories", "directories"),
                    ("patterns", "patterns"),
                    ("files", "files"),
                    ("pre_commands", "pre_commands"),
                ]:
                    val = prof.get(key, [])
                    if val:
                        print(f"  {label}: {', '.join(val)}")
                print(f"  max_tokens: {prof.get('max_tokens', '?')}")
                print(f"  split_mode: {prof.get('split_mode', '?')}")
            else:
                print(f"Profile: {prof} (legacy format)")
            return

        if stats_only:
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
            for key, label in [
                ("directories", "directories"),
                ("patterns", "patterns"),
                ("files", "files"),
                ("pre_commands", "pre_commands"),
            ]:
                val = prof.get(key, [])
                if val:
                    print(f"  {label}: {', '.join(val)}")
            print(f"  max_tokens: {prof.get('max_tokens', '?')}")
            print(f"  split_mode: {prof.get('split_mode', '?')}")
        else:
            print(f"Profile: {prof} (legacy format)")
        return

    if "rename" in argv:
        idx = argv.index("rename")
        if idx + 2 >= len(argv):
            print("Usage: arachna --snapshot rename <old> <new>")
            sys.exit(1)
        old_id = argv[idx + 1]
        new_id = argv[idx + 2]
        if old_id.startswith("-") or new_id.startswith("-"):
            print("Usage: arachna --snapshot rename <old> <new>")
            sys.exit(1)
        try:
            validate_snapshot_id(old_id)
            validate_snapshot_id(new_id)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        try:
            store_rename_snapshot(old_id, new_id)
            print(f"Snapshot '{old_id}' renamed to '{new_id}'.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    if "delete" in argv:
        idx = argv.index("delete")
        if idx + 1 < len(argv):
            sid = argv[idx + 1]
            try:
                validate_snapshot_id(sid)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)
            try:
                delete_snapshot(sid)
                print(f"Snapshot '{sid}' deleted.")
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)
        else:
            print("Usage: arachna --snapshot delete <id>")
            sys.exit(1)
        return

    if "create" in argv:
        profile_name = None
        if "--profile" in argv:
            idx = argv.index("--profile")
            if idx + 1 < len(argv):
                val = argv[idx + 1]
                if val.startswith("-"):
                    print("Error: --profile requires a value")
                    sys.exit(1)
                profile_name = val
            else:
                print("Error: --profile requires a value")
                sys.exit(1)
        name = None
        if "--name" in argv:
            idx = argv.index("--name")
            if idx + 1 < len(argv):
                val = argv[idx + 1]
                if val.startswith("-"):
                    print("Error: --name requires a value")
                    sys.exit(1)
                name = val
            else:
                print("Error: --name requires a value")
                sys.exit(1)
        if not name:
            print("Error: --name is required for 'create'.")
            sys.exit(1)
        try:
            validate_snapshot_id(name)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        profile = get_profile(profile_name) if profile_name else get_profile("full")
        try:
            sid = watch_create_snapshot(profile, name=name)
            print(f"Snapshot '{sid}' created.")
        except SnapshotExistsError as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    if "update" in argv:
        idx = argv.index("update")
        if idx + 1 >= len(argv):
            print("Usage: arachna --snapshot update <id> [--profile X]")
            sys.exit(1)
        sid = argv[idx + 1]
        if sid.startswith("-"):
            print(f"Error: invalid snapshot ID '{sid}'")
            sys.exit(1)
        try:
            validate_snapshot_id(sid)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)
        profile = None
        if "--profile" in argv:
            profile_idx = argv.index("--profile")
            if profile_idx + 1 < len(argv):
                val = argv[profile_idx + 1]
                if val.startswith("-"):
                    print("Error: --profile requires a value")
                    sys.exit(1)
                profile = get_profile(val)
            else:
                print("Error: --profile requires a value")
                sys.exit(1)
        try:
            watch_update_snapshot(sid, profile=profile)
            print(f"Snapshot '{sid}' updated.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    print("Usage: arachna --snapshot <command>")
    print()
    print("Commands:")
    print("  list                List all snapshots")
    print("  info <id>           Show snapshot details")
    print("  info <id> --profile Show profile only")
    print("  info <id> --stats   Show stats only")
    print("  create --profile X --name Y")
    print("                      Create a named snapshot")
    print("  update <id> [--profile X]")
    print("                      Update an existing snapshot")
    print("  delete <id>         Delete a snapshot")
    print("  rename <old> <new>  Rename a snapshot")
    print()
    print("Examples:")
    print("  arachna --snapshot list")
    print("  arachna --snapshot info cycle")
    print("  arachna --snapshot create --profile code --name before-refactor")
    print("  arachna --snapshot update before-refactor")
    print("  arachna --snapshot rename before-refactor after-refactor")
    print("  arachna --snapshot delete before-refactor")


def _cmd_diff(argv: list[str]):
    from .store import list_snapshots, load_snapshot
    from .watcher import compute_diff

    if "--all" in argv and "--from" in argv:
        print("Error: Cannot use --all and --from together.")
        print("  --diff --all         full project as diff (no snapshot)")
        print("  --diff --from <id>   diff from a specific snapshot")
        sys.exit(1)

    if "--all" in argv:
        _cmd_diff_all(argv)
        return

    snapshot_id = None
    if "--from" in argv:
        idx = argv.index("--from")
        if idx + 1 < len(argv):
            snapshot_id = argv[idx + 1]
        else:
            print("Error: --from requires a snapshot ID")
            sys.exit(1)

    to_snapshot_id = None
    if "--to" in argv:
        idx = argv.index("--to")
        if idx + 1 < len(argv):
            to_snapshot_id = argv[idx + 1]
        else:
            print("Error: --to requires a snapshot ID")
            sys.exit(1)

    profile = None
    if "--profile" in argv:
        idx = argv.index("--profile")
        if idx + 1 < len(argv):
            profile = get_profile(argv[idx + 1])
        else:
            print("Error: --profile requires a value")
            sys.exit(1)

    fmt = "markdown"
    if "--format" in argv:
        idx = argv.index("--format")
        if idx + 1 < len(argv):
            fmt = argv[idx + 1]
        else:
            print("Error: --format requires a value")
            sys.exit(1)

    stat_only = "--stat" in argv
    flat_mode = "--flat" in argv

    diff_mode = "full"
    if "--mode" in argv:
        idx = argv.index("--mode")
        if idx + 1 < len(argv):
            diff_mode = argv[idx + 1]

    if snapshot_id is None:
        snaps = list_snapshots()
        if len(snaps) == 0:
            print("Error: No snapshots found.")
            sys.exit(1)
        elif len(snaps) == 1:
            snapshot_id = snaps[0]["id"]
        else:
            print("Error: Multiple snapshots found. Use --from to specify which one:")
            for s in snaps:
                print(f"  arachna --diff --from {s['id']:20} # {s.get('name', s['id'])}")
            sys.exit(1)

    config = load_config()
    output_dir = _parse_output_dir(argv, config)

    project_name = config.get("project_name", "Project")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if profile is None:
        manifest = load_snapshot(snapshot_id)
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile = stored
        else:
            print(f"Error: Snapshot '{snapshot_id}' has legacy format. Use --profile.")
            sys.exit(1)

    if "--compress" in argv:
        profile["compress"] = True

    sections = compute_diff(
        snapshot_id, profile, fmt=fmt, to_snapshot_id=to_snapshot_id, flat=flat_mode
    )

    if stat_only:
        stats = compute_diff_stats(sections)
        print(f"Modified: {stats['modified']}")
        print(f"Added:    {stats['added']}")
        print(f"Deleted:  {stats['deleted']}")
        if stats["renamed"]:
            print(f"Renamed:  {stats['renamed']}")
        if stats["moved"]:
            print(f"Moved:    {stats['moved']}")
        print(f"Tokens:   {stats['tokens']}")
        return

    if not sections:
        print("No changes since snapshot.")
        return

    if diff_mode == "structural":
        from .differ_structural import structural_diff_sections

        sections = structural_diff_sections(sections, fmt)
    elif diff_mode == "repo-map":
        from .gatherer import _apply_repo_map_to_sections

        sections = _apply_repo_map_to_sections(sections, snapshot_id, to_snapshot_id, profile)

    content_sections = [s for s in sections if s.content.strip()]
    if not content_sections:
        print("No changes since snapshot.")
        return

    max_tokens = profile.get("max_tokens", 16000)
    tokenizer_spec = profile.get("tokenizer", "default")
    tokenizer = load_tokenizer(tokenizer_spec) if tokenizer_spec != "default" else count_tokens

    if to_snapshot_id:
        name_tmpl = f"chat-diff-{snapshot_id}-to-{to_snapshot_id}"
        title_tmpl = f"# {project_name} — DIFF from {snapshot_id} to {to_snapshot_id} (part {{part}} of {{total}})\n\n"
    else:
        name_tmpl = f"chat-diff-{snapshot_id}"
        title_tmpl = f"# {project_name} — DIFF from {snapshot_id} (part {{part}} of {{total}})\n\n"

    clean_manifest(out_path, name_tmpl)
    created = _write_diff_parts(
        content_sections,
        out_path,
        name_tmpl,
        title_tmpl,
        project_name,
        max_tokens,
        tokenizer,
        snapshot_id=snapshot_id,
        to_snapshot_id=to_snapshot_id,
    )
    _print_collected(created)
    prev = load_manifest(out_path)
    updated = [f for f in prev if not f.startswith(name_tmpl)]
    updated.extend(created)
    save_manifest(out_path, updated)


def _cmd_diff_all(argv: list[str]):
    config = load_config()
    project_name = config.get("project_name", "Project")
    output_dir = _parse_output_dir(argv, config)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    profile_name = "full"
    if "--profile" in argv:
        idx = argv.index("--profile")
        if idx + 1 < len(argv):
            profile_name = argv[idx + 1]

    diff_mode = "full"
    if "--mode" in argv:
        idx = argv.index("--mode")
        if idx + 1 < len(argv):
            diff_mode = argv[idx + 1]

    query = None
    if "--query" in argv:
        idx = argv.index("--query")
        if idx + 1 < len(argv):
            query = argv[idx + 1]

    compress = "--compress" in argv

    profile = get_profile(profile_name)
    if compress:
        profile["compress"] = True

    name_tmpl = "chat-diff-all"

    clean_manifest(out_path, name_tmpl)

    created, tokens_by_file = collect(
        profile,
        project_name,
        str(out_path),
        verbose=False,
        incremental=False,
        merge=False,
        query=query,
        mode=diff_mode,
        name_template=name_tmpl,
    )

    if created:
        _print_collected(created)
        prev = load_manifest(out_path)
        updated = [f for f in prev if not f.startswith("chat-diff-all")]
        updated.extend(created)
        save_manifest(out_path, updated)
    else:
        print("  No content collected.")


def _cmd_store(argv: list[str]):
    from .store import gc, stats

    cmd = None
    if "gc" in argv:
        cmd = "gc"
    elif "stats" in argv:
        cmd = "stats"
    if cmd == "gc":
        result = gc()
        if result["removed"] == 0:
            print("No objects to collect.")
        else:
            print(f"Removed {result['removed']} objects (freed {result['freed_bytes']} bytes).")
    elif cmd == "stats":
        s = stats()
        print("Store statistics:")
        print(f"  Snapshots: {s['snapshots']}")
        print(f"  Objects: {s['objects']}")
        print(f"  Total size: {s['total_bytes']} bytes")
        print(f"  Unique content: {s['unique_bytes']} bytes ({s['dedup_pct']}% deduplication)")
    else:
        print("Usage: arachna --store gc|stats")
        sys.exit(1)


def _print_collected(created: list[str]):
    if created:
        for f in created:
            content = Path(f).read_text(encoding="utf-8")
            lines = content.count("\n") + 1
            tokens = count_tokens(content)
            print(f"  {Path(f).name} ({lines} lines, ~{tokens} tokens)")
    else:
        print("  No content collected.")
