"""CLI entry point for arachna v3.0.0 — argparse subparsers."""

import argparse
import copy
import json
import sys
from pathlib import Path

from . import __version__
from .collector import (
    _MANIFEST,
    clean_manifest,
    collect,
    load_manifest,
    save_manifest,
)
from .config import get_profile, load_config
from .gatherer import dry_run
from .renderer import render_dry_run
from .tokenizer import count_tokens, load_tokenizer
from .validator import validate_profile

# ── Helpers ────────────────────────────────────────────────────────


def _list_profiles(config: dict) -> list[str]:
    profiles = config.get("profiles", {})
    if profiles:
        return list(profiles.keys())
    return ["default"]


def _apply_args_to_profile(profile: dict, args):
    profile = copy.deepcopy(profile)
    if getattr(args, "compress", False):
        profile["compress"] = True
    if getattr(args, "format", None):
        profile["section_format"] = args.format
    return profile


def _parse_output_dir(args, config: dict) -> str:
    if getattr(args, "output_dir", None):
        return args.output_dir
    return config.get("output_dir", ".")


def _print_collected(created: list[str]):
    if created:
        for f in created:
            content = Path(f).read_text(encoding="utf-8")
            lines = content.count("\n") + 1
            tokens = count_tokens(content)
            print(f"  {Path(f).name} ({lines} lines, ~{tokens} tokens)")
    else:
        print("  No content collected.")


def _write_manifest(
    out_path: Path, all_files: list[str], tokens_by_file: dict[str, int], config: dict
):
    lines = [
        f"# {config.get('project_name', 'Project')} — MANIFEST\n",
        "\nAll collected files:\n",
    ]
    for f in sorted(all_files):
        tokens = tokens_by_file.get(f, 0)
        lines.append(f"  {f} (~{tokens} tokens)")
    lines.append(f"\nTotal: {len(all_files)} file(s)\n")
    mf = out_path / "chat-manifest.md"
    mf.write_text("\n".join(lines))
    print(f"  chat-manifest.md ({len(all_files)} files)")


# ── Collect handlers ──────────────────────────────────────────────


def _cmd_collect_profile(args, config: dict):
    project_name = config.get("project_name", "Project")
    output_dir = _parse_output_dir(args, config)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"[{args.profile}] Collecting...")
    try:
        profile = get_profile(args.profile)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    profile = _apply_args_to_profile(profile, args)

    if getattr(args, "no_pre_commands", False):
        profile["pre_commands"] = []

    if args.dry_run:
        query = getattr(args, "query", None)
        mode = getattr(args, "mode", "full")
        stats = dry_run(profile, query=query, mode=mode)
        stats["name"] = args.profile
        render_dry_run([stats])
        return

    name_tmpl = profile.get("name_template", f"chat-{args.profile}")

    if not args.merge:
        clean_manifest(out_path, name_tmpl)

    created, tokens_by_file, _parts = collect(
        profile,
        project_name,
        str(out_path),
        verbose=args.verbose,
        incremental=args.incremental,
        merge=args.merge,
        query=getattr(args, "query", None),
        mode=getattr(args, "mode", "full"),
    )

    prev = load_manifest(out_path)
    if args.merge:
        updated = list(prev)
        for f in created:
            if f not in updated:
                updated.append(f)
    else:
        updated = [f for f in prev if not f.startswith(name_tmpl)]
        updated.extend(created)
    save_manifest(out_path, updated)

    _print_collected(created)


def _cmd_collect_all(args, config: dict):
    project_name = config.get("project_name", "Project")
    output_dir = _parse_output_dir(args, config)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    clean_manifest(out_path, "")
    all_created = []
    all_tokens = {}
    for name in _list_profiles(config):
        print(f"[{name}] Collecting...")
        try:
            profile = get_profile(name)
        except KeyError:
            continue
        profile = _apply_args_to_profile(profile, args)

        if getattr(args, "no_pre_commands", False):
            profile["pre_commands"] = []

        if args.dry_run:
            query = getattr(args, "query", None)
            mode = getattr(args, "mode", "full")
            stats = dry_run(profile, query=query, mode=mode)
            stats["name"] = name
            all_created_stats = getattr(args, "_all_stats", None)
            if all_created_stats is None:
                all_created_stats = []
                args._all_stats = all_created_stats
            all_created_stats.append(stats)
            continue

        name_tmpl = profile.get("name_template", f"chat-{name}")
        clean_manifest(out_path, name_tmpl)

        created, tokens_by_file, _parts = collect(
            profile,
            project_name,
            str(out_path),
            verbose=args.verbose,
            incremental=args.incremental,
            merge=False,
            query=getattr(args, "query", None),
            mode=getattr(args, "mode", "full"),
        )

        if created:
            all_created.extend(created)
            all_tokens.update(tokens_by_file)
            _print_collected(created)
        else:
            print("  No content collected.")

    if args.dry_run:
        all_stats = getattr(args, "_all_stats", [])
        if all_stats:
            render_dry_run(all_stats)
        return

    if all_created:
        _write_manifest(out_path, all_created, all_tokens, config)
        all_created.append("chat-manifest.md")
        save_manifest(out_path, all_created)


def _cmd_collect_list(args, config: dict):
    for name in _list_profiles(config):
        try:
            prof = get_profile(name)
        except KeyError:
            continue
        cmd = prof.get("command")
        if cmd:
            print(f"  {name}: command ({prof.get('max_tokens', '?')} tokens)")
        else:
            dirs = len(prof.get("directories", []))
            files = len(prof.get("files", []))
            print(f"  {name}: {dirs} dirs, {files} files ({prof.get('max_tokens', '?')} tokens)")


def _cmd_collect_validate(args, config: dict):
    profiles = config.get("profiles", {})
    if not profiles:
        profiles = {"default": get_profile("default")}
    else:
        valid_profiles = {}
        for name in profiles:
            try:
                valid_profiles[name] = get_profile(name)
            except KeyError as e:
                print(f"  ✗ Profile '{name}': {e}")
        profiles = valid_profiles
    all_errors = 0
    all_warnings = 0
    for name, prof in profiles.items():
        result = validate_profile(name, prof)
        errors = result["errors"]
        warnings = result["warnings"]
        if errors or warnings:
            print(f"\n[{name}]")
            for e in errors:
                print(f"  ✗ {e}")
            for w in warnings:
                print(f"  ⚠ {w}")
            all_errors += len(errors)
            all_warnings += len(warnings)
        else:
            print(f"  [{name}] ✓ valid")
    print(f"\nResult: {all_errors} error(s), {all_warnings} warning(s)")
    sys.exit(1 if all_errors > 0 else 0)


def _cmd_collect_clean(args, config: dict):
    output_dir = _parse_output_dir(args, config)
    out_path = Path(output_dir)
    cleaned = 0
    mf = out_path / _MANIFEST
    if mf.exists():
        try:
            manifest = json.loads(mf.read_text())
            for f in manifest.get("files", []):
                p = out_path / f
                if p.exists():
                    p.unlink()
                    cleaned += 1
                    print(f"  Removed: {f}")
        except (json.JSONDecodeError, OSError):
            pass
        mf.unlink()
        cleaned += 1
        print(f"  Removed: {_MANIFEST}")
    for pattern in ["chat-*_*.md", "chat-*.md", "chat-diff*.md", "chat-diff*_*.md"]:
        for f in out_path.glob(pattern):
            f.unlink()
            cleaned += 1
            print(f"  Removed: {f.name}")
    print(f"Cleaned {cleaned} file(s).")


# ── Snapshot handlers ─────────────────────────────────────────────


def _cmd_snapshot_create(args, config: dict):
    from .store import validate_snapshot_id
    from .store_errors import SnapshotExistsError
    from .watcher import create_snapshot as watch_create_snapshot

    if not args.name:
        print("Error: --name is required for 'create'.")
        sys.exit(1)
    try:
        validate_snapshot_id(args.name)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    profile_name = args.profile or "full"
    try:
        profile = get_profile(profile_name)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        sid = watch_create_snapshot(profile, name=args.name)
        print(f"Snapshot '{sid}' created.")
    except SnapshotExistsError as e:
        print(f"Error: {e}")
        sys.exit(1)


def _cmd_snapshot_list(args, config: dict):
    from .store import list_snapshots

    snaps = list_snapshots()
    if not snaps:
        print("No snapshots found.")
        return
    print("Snapshots:")
    for s in snaps:
        created = s.get("created", "?")
        file_count = len(s.get("files", {}))
        print(f"  {s['id']:30} {created:25} {file_count} files")


def _cmd_snapshot_update(args, config: dict):
    from .store import validate_snapshot_id
    from .watcher import update_snapshot as watch_update_snapshot

    sid = args.id
    try:
        validate_snapshot_id(sid)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    profile = None
    if args.profile:
        try:
            profile = get_profile(args.profile)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)

    try:
        watch_update_snapshot(sid, profile=profile)
        print(f"Snapshot '{sid}' updated.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def _cmd_snapshot_delete(args, config: dict):
    from .store import delete_snapshot, validate_snapshot_id

    sid = args.id
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


def _cmd_snapshot_info(args, config: dict):
    from .store import list_snapshots, validate_snapshot_id

    sid = args.id
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

    if args.profile_only:
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


def _cmd_snapshot_rename(args, config: dict):
    from .store import rename_snapshot as store_rename_snapshot
    from .store import validate_snapshot_id

    try:
        validate_snapshot_id(args.old)
        validate_snapshot_id(args.new)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        store_rename_snapshot(args.old, args.new)
        print(f"Snapshot '{args.old}' renamed to '{args.new}'.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


# ── Diff handlers ─────────────────────────────────────────────────


def _cmd_diff(args, config: dict):
    from .collector import _write_diff_parts, clean_manifest, load_manifest, save_manifest
    from .differ import compute_diff_stats
    from .store import list_snapshots, load_snapshot
    from .watcher import compute_diff

    if args.all and args.from_snapshot:
        print("Error: Cannot use --all and --from together.")
        print("  arachna diff --all         full project as diff (no snapshot)")
        print("  arachna diff --from <id>   diff from a specific snapshot")
        sys.exit(1)

    if args.all:
        _cmd_diff_all(args, config)
        return

    snapshot_id = args.from_snapshot

    to_snapshot_id = args.to

    profile = None
    if args.profile:
        try:
            profile = get_profile(args.profile)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)

    fmt = args.format or "markdown"
    stat_only = args.stat
    flat_mode = args.flat
    diff_mode = args.mode or "full"

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
                print(f"  arachna diff --from {s['id']:20} # {s.get('name', s['id'])}")
            sys.exit(1)

    output_dir = _parse_output_dir(args, config)
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

    if args.compress:
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


def _cmd_diff_all(args, config: dict):
    from .collector import clean_manifest, collect, load_manifest, save_manifest

    project_name = config.get("project_name", "Project")
    output_dir = _parse_output_dir(args, config)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    profile_name = args.profile or "full"
    diff_mode = args.mode or "full"
    query = args.query
    compress = args.compress

    try:
        profile = get_profile(profile_name)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if compress:
        profile["compress"] = True

    name_tmpl = "chat-diff-all"

    clean_manifest(out_path, name_tmpl)

    created, tokens_by_file, _parts = collect(
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


# ── Store handlers ────────────────────────────────────────────────


def _cmd_store_stats(args, config: dict):
    from .store import stats

    s = stats()
    print("Store statistics:")
    print(f"  Snapshots: {s['snapshots']}")
    print(f"  Objects: {s['objects']}")
    print(f"  Total size: {s['total_bytes']} bytes")
    print(f"  Unique content: {s['unique_bytes']} bytes ({s['dedup_pct']}% deduplication)")


def _cmd_store_gc(args, config: dict):
    from .store import gc

    result = gc()
    if result["removed"] == 0:
        print("No objects to collect.")
    else:
        print(f"Removed {result['removed']} objects (freed {result['freed_bytes']} bytes).")


# ── Other handlers ────────────────────────────────────────────────


def _cmd_doctor(args, config: dict):
    from .doctor import print_doctor, run_doctor

    report = run_doctor()
    print_doctor(report)
    sys.exit(1 if report["total_errors"] > 0 else 0)


def _cmd_init(args, config: dict):
    from .init import run_defaults, run_interactive

    output_dir = _parse_output_dir(args, config)
    if args.defaults:
        run_defaults(output_dir, preset=args.preset)
    else:
        run_interactive(output_dir, preset=args.preset)


def _cmd_completion(args, config: dict):
    from .completion import generate_bash, generate_zsh

    shell = args.shell
    if shell == "bash":
        generate_bash()
    elif shell == "zsh":
        generate_zsh()
    else:
        print("Usage: arachna completion bash|zsh")
        print("  source <(arachna completion bash)")
        print("  source <(arachna completion zsh)")


def _cmd_presets_update(args, config: dict):
    from .presets import _load_builtin_presets, fetch_presets, load_presets_from_file, merge_presets

    url = args.url or "https://raw.githubusercontent.com/dead-duke/arachna/main/presets.json"
    if not url.startswith(("http://", "https://")):
        print("Error: only http:// and https:// URLs are allowed for security reasons.")
        print(f"  Got: {url}")
        sys.exit(1)

    local = load_presets_from_file("presets.json")
    if local:
        print(f"Local presets.json: {len(local)} preset(s) — will be preserved.")
    elif Path("presets.json").exists():
        print("Warning: local presets.json exists but could not be loaded. Aborting.")
        print("  Fix or remove the file and try again.")
        sys.exit(1)

    print(f"Fetching presets from {url}...")
    remote = fetch_presets(url)
    if not remote:
        print("No presets fetched. Check URL or network.")
        sys.exit(1)

    builtin = _load_builtin_presets()
    merged = merge_presets(builtin, remote, local)

    out = json.dumps(merged, indent=2) + "\n"
    Path("presets.json").write_text(out)
    new_count = len(remote)
    local_count = len(local)
    print(
        f"Presets updated: {len(merged)} total ({new_count} remote, {local_count} local preserved)."
    )
    print("Saved to presets.json")


# ── Plugin handlers ────────────────────────────────────────────────


def _cmd_plugins_list(args, config: dict):
    from .plugins import list_plugins

    plugins = list_plugins()
    if not plugins:
        print("No plugins available.")
        return

    print("Plugins:")
    for name, info in sorted(plugins.items()):
        status = "installed" if info["installed"] else "not installed"
        deps = ", ".join(info["deps"])
        print(f"  {name:15} {status:15} ({deps})")


def _cmd_plugins_install(args, config: dict):
    from .plugins import install_plugin

    result = install_plugin(args.language, execute=args.execute)
    print(result)


def _cmd_plugins_uninstall(args, config: dict):
    from .plugins import uninstall_plugin

    result = uninstall_plugin(args.language)
    print(result)


# ── Main ──────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="arachna — context collector for AI",
    )
    parser.add_argument("--version", action="version", version=f"arachna v{__version__}")

    sub = parser.add_subparsers(dest="command")

    # ── collect ────────────────────────────────────────────────
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

    # ── snapshot ───────────────────────────────────────────────
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

    # ── diff ───────────────────────────────────────────────────
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

    # ── store ──────────────────────────────────────────────────
    store_p = sub.add_parser("store", help="Store management")
    store_subs = store_p.add_subparsers(dest="store_command")
    store_subs.add_parser("stats", help="Show store statistics")
    store_subs.add_parser("gc", help="Garbage collect store")

    # ── plugins ────────────────────────────────────────────────
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

    # ── presets ────────────────────────────────────────────────
    presets_p = sub.add_parser("presets", help="Preset management")
    presets_subs = presets_p.add_subparsers(dest="presets_command")
    presets_update = presets_subs.add_parser("update", help="Update presets from remote")
    presets_update.add_argument("--url", help="Remote presets URL")

    # ── doctor ─────────────────────────────────────────────────
    sub.add_parser("doctor", help="Run configuration diagnostic")

    # ── init ───────────────────────────────────────────────────
    init_p = sub.add_parser("init", help="Create .arachna.json interactively")
    init_p.add_argument("--defaults", action="store_true", help="Use defaults (non-interactive)")
    init_p.add_argument("--preset", help="Use specific preset")
    init_p.add_argument("--install-hook", action="store_true", help="Install post-commit git hook")
    init_p.add_argument("--force", action="store_true")
    init_p.add_argument("--output-dir", "-o", help="Output directory")

    # ── completion ─────────────────────────────────────────────
    comp_p = sub.add_parser("completion", help="Generate shell completion")
    comp_p.add_argument("shell", nargs="?", choices=["bash", "zsh"], help="Shell: bash or zsh")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    config = load_config()

    # ── Dispatch ──────────────────────────────────────────────────

    if args.command == "collect":
        if args.list:
            _cmd_collect_list(args, config)
        elif args.validate:
            _cmd_collect_validate(args, config)
        elif args.clean:
            _cmd_collect_clean(args, config)
        elif args.all:
            _cmd_collect_all(args, config)
        elif args.profile:
            _cmd_collect_profile(args, config)
        else:
            collect_p.print_help()
            sys.exit(1)

    elif args.command == "snapshot":
        snap_cmd = getattr(args, "snap_command", None)
        if snap_cmd == "create":
            _cmd_snapshot_create(args, config)
        elif snap_cmd == "list":
            _cmd_snapshot_list(args, config)
        elif snap_cmd == "update":
            _cmd_snapshot_update(args, config)
        elif snap_cmd == "delete":
            _cmd_snapshot_delete(args, config)
        elif snap_cmd == "info":
            _cmd_snapshot_info(args, config)
        elif snap_cmd == "rename":
            _cmd_snapshot_rename(args, config)
        else:
            snap_p.print_help()
            sys.exit(1)

    elif args.command == "diff":
        _cmd_diff(args, config)

    elif args.command == "store":
        store_cmd = getattr(args, "store_command", None)
        if store_cmd == "stats":
            _cmd_store_stats(args, config)
        elif store_cmd == "gc":
            _cmd_store_gc(args, config)
        else:
            store_p.print_help()
            sys.exit(1)

    elif args.command == "plugins":
        plugins_cmd = getattr(args, "plugins_command", None)
        if plugins_cmd == "list":
            _cmd_plugins_list(args, config)
        elif plugins_cmd == "install":
            _cmd_plugins_install(args, config)
        elif plugins_cmd == "uninstall":
            _cmd_plugins_uninstall(args, config)
        else:
            plugins_p.print_help()
            sys.exit(1)

    elif args.command == "presets":
        presets_cmd = getattr(args, "presets_command", None)
        if presets_cmd == "update":
            _cmd_presets_update(args, config)
        else:
            presets_p.print_help()
            sys.exit(1)

    elif args.command == "doctor":
        _cmd_doctor(args, config)

    elif args.command == "init":
        if args.install_hook:
            from .hook import install_hook

            success, msg = install_hook(force=args.force)
            print(msg)
            sys.exit(0 if success else 1)
        else:
            _cmd_init(args, config)

    elif args.command == "completion":
        _cmd_completion(args, config)


if __name__ == "__main__":
    main()
