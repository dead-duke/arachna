"""CLI entry point for arachna."""

import argparse
import copy
import json
import sys
from pathlib import Path

from . import __version__
from .collector import _MANIFEST, clean_manifest, collect, load_manifest, save_manifest
from .config import get_profile, load_config
from .gatherer import _assemble_content, _get_exclude_patterns, dry_run
from .renderer import render_dry_run
from .splitter import split_sections
from .tokenizer import count_tokens, load_tokenizer
from .validator import validate_profile


def _list_profiles(config: dict) -> list[str]:
    profiles = config.get("profiles", {})
    if profiles:
        return list(profiles.keys())
    return ["default"]


def _collect_profile_names(config: dict, args) -> list[str]:
    """Get list of profile names to process based on args."""
    if args.all:
        return _list_profiles(config)
    return [args.profile]


def _apply_args_to_profile(profile: dict, args):
    """Apply CLI args to profile dict (compress, format).

    Returns a deep copy — does not mutate the original.
    """
    profile = copy.deepcopy(profile)
    if args.compress:
        profile["compress"] = True
    if args.format:
        profile["section_format"] = args.format
    return profile


def _run_profile(name: str, config: dict, args, project_name: str, out_path: Path):
    """Collect a single profile. Returns (created_files, tokens_by_file) tuple, or stats dict for dry-run."""
    try:
        profile = get_profile(name)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    profile = _apply_args_to_profile(profile, args)

    if args.dry_run:
        stats = dry_run(profile)
        stats["name"] = name
        return stats, {}

    name_tmpl = profile.get("name_template", f"chat-{name}")

    # In merge mode, don't clean old files
    if not args.merge:
        clean_manifest(out_path, name_tmpl)

    created, tokens_by_file = collect(
        profile,
        project_name,
        str(out_path),
        verbose=args.verbose,
        incremental=args.incremental,
        merge=args.merge,
    )

    if not args.all:
        prev = load_manifest(out_path)
        if args.merge:
            # Keep all existing files, add new ones
            updated = list(prev)
            for f in created:
                if f not in updated:
                    updated.append(f)
        else:
            # Replace files for this profile
            updated = [f for f in prev if not f.startswith(name_tmpl)]
            updated.extend(created)
        save_manifest(out_path, updated)

    return created, tokens_by_file


def _combine_full_and_diff(
    full_parts: list[str],
    diff_sections: list,
    snapshot_id: str,
    project_name: str,
    title_tmpl: str,
    max_tokens: int,
    out_path: Path,
    tokenizer,
) -> list[str]:
    """Merge full context parts and diff sections into a single output.

    Output format:
        # Project — FULL CONTEXT + DIFF (part {part})

        ## Full Context
        <context parts>

        ---

        ## Changes since snapshot <id>
        <diff sections>

    Returns list of created file paths.
    """
    # Build diff content from sections
    if diff_sections:
        diff_content = "\n".join(s.content for s in diff_sections)
    else:
        diff_content = "No changes since snapshot."

    # Combine: each full part + separator + diff in one block
    # then split by tokens
    separator = "\n\n---\n\n## Changes since snapshot " + snapshot_id + "\n\n"
    combined_sections = []
    for i, part in enumerate(full_parts):
        header = title_tmpl.format(project_name=project_name, part=i + 1, total=len(full_parts))
        body = "## Full Context\n\n" + part + separator
        if i == 0:
            # First part includes diff
            body += diff_content
        combined_sections.append(header + body)

    # Split combined sections by token limit
    all_content = "\n\n".join(combined_sections)
    final_parts = split_sections([all_content], max_tokens, separator="\n\n", tokenizer=tokenizer)

    # Write output files
    created = []
    name_tmpl = "chat-diff-full"
    total_parts = len(final_parts)
    for i, part_content in enumerate(final_parts, 1):
        filename = f"{name_tmpl}.md" if total_parts == 1 else f"{name_tmpl}_{i}.md"
        filepath = out_path / filename

        title = f"# {project_name} — FULL CONTEXT + DIFF (part {i} of {total_parts})\n\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(title)
            f.write(part_content)

        created.append(str(filepath))

    return created


def _cmd_diff_full(
    snapshot_id: str,
    profile_name: str | None,
    config: dict,
    args,
    project_name: str,
    out_path: Path,
):
    """Handle --diff --full: collect full context + diff, combine into single output."""
    # Get profile
    profile = get_profile(profile_name) if profile_name else get_profile("full")
    profile = _apply_args_to_profile(profile, args)

    # Load tokenizer
    tokenizer_spec = profile.get("tokenizer", "default")
    tokenizer = load_tokenizer(tokenizer_spec) if tokenizer_spec != "default" else count_tokens

    # Collect full context
    exclude = _get_exclude_patterns(profile)
    named_sections, full_parts, _ = _assemble_content(
        profile,
        exclude,
        tokenizer,
        incremental=False,
        cache=None,
        verbose=args.verbose,
    )

    if not full_parts:
        print("No content collected for full context.")
        return

    # Compute diff
    from .watcher import compute_diff

    diff_sections = compute_diff(snapshot_id, profile)

    if not diff_sections:
        print("No changes since snapshot.")

    # Combine and write
    title_tmpl = profile.get(
        "title_template", f"# {project_name} — FULL CONTEXT + DIFF (part {{part}})\n\n"
    )
    max_tokens = profile.get("max_tokens", 32768)
    name_tmpl = "chat-diff-full"

    # Clean old diff-full files
    clean_manifest(out_path, name_tmpl)

    created = _combine_full_and_diff(
        full_parts,
        diff_sections,
        snapshot_id,
        project_name,
        title_tmpl,
        max_tokens,
        out_path,
        tokenizer,
    )

    # Print summary
    for f in created:
        filepath = Path(f)
        content = filepath.read_text(encoding="utf-8")
        lines = content.count("\n") + 1
        tokens = tokenizer(content)
        print(f"  {filepath.name} ({lines} lines, ~{tokens} tokens)")

    # Update manifest
    prev = load_manifest(out_path)
    updated = [f for f in prev if not f.startswith(name_tmpl)]
    updated.extend(created)
    save_manifest(out_path, updated)


def main():
    # Handle --completion before argparse (requires interactive output)
    if "--completion" in sys.argv:
        from .completion import main as completion_main

        idx = sys.argv.index("--completion")
        shell = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        sys.argv = ["completion", shell]
        completion_main()
        return

    # Handle --snapshot before argparse
    if "--snapshot" in sys.argv:
        _cmd_snapshot(sys.argv)
        return

    # Handle --diff before argparse
    if "--diff" in sys.argv:
        _cmd_diff(sys.argv)
        return

    # Handle --store before argparse
    if "--store" in sys.argv:
        _cmd_store(sys.argv)
        return

    parser = argparse.ArgumentParser(description="arachna — context collector for AI")
    parser.add_argument("--version", action="version", version=f"arachna v{__version__}")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile", "-p", help="Profile name to collect")
    group.add_argument("--all", "-a", action="store_true", help="Collect all profiles")
    group.add_argument("--clean", "-c", action="store_true", help="Remove all collected files")
    group.add_argument("--list", "-l", action="store_true", help="List available profiles")
    group.add_argument("--validate", action="store_true", help="Validate config for errors")
    group.add_argument("--init", action="store_true", help="Create .arachna.json interactively")
    group.add_argument("--doctor", action="store_true", help="Run configuration diagnostic")
    group.add_argument("--install-hook", action="store_true", help="Install post-commit git hook")
    group.add_argument("--snapshot", action="store_true", help="Create or manage snapshots")
    group.add_argument("--diff", action="store_true", help="Compute diff from snapshot")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what will be collected without writing"
    )
    parser.add_argument("--output-dir", "-o", help="Override output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show skipped files")
    parser.add_argument(
        "--compress", action="store_true", help="Compress whitespace to save tokens"
    )
    parser.add_argument("--incremental", action="store_true", help="Only collect changed files")
    parser.add_argument("--format", choices=["markdown", "xml", "json"], help="Output format")
    parser.add_argument("--defaults", action="store_true", help="Use defaults with --init")
    parser.add_argument(
        "--merge", action="store_true", help="Append to existing output instead of replacing"
    )
    parser.add_argument("--force", action="store_true", help="Force overwrite with --install-hook")
    parser.add_argument("--preset", help="Use specific preset with --init (e.g. godot, unity)")
    parser.add_argument("--name", help="Snapshot name")
    parser.add_argument("--from", dest="from_snapshot", help="Snapshot ID to diff from")
    parser.add_argument("--store", help="Store command: gc or stats")
    parser.add_argument("--full", action="store_true", help="Combine full context with --diff")

    args = parser.parse_args()
    config = load_config()
    project_name = config.get("project_name", "Project")
    output_dir = args.output_dir or config.get("output_dir", ".")
    out_path = Path(output_dir)

    # Dispatch: determine action from args and call handler directly
    if args.init:
        _cmd_init(args, output_dir)
    elif args.list:
        _cmd_list(config)
    elif args.validate:
        _cmd_validate(config)
    elif args.doctor:
        _cmd_doctor()
    elif args.install_hook:
        _cmd_install_hook(args)
    elif args.clean:
        _cmd_clean(config, out_path)
    elif args.dry_run and (args.all or args.profile):
        _cmd_dry_run(config, args)
    elif args.all:
        _cmd_all(config, args, project_name, out_path)
    else:
        _cmd_single(config, args, project_name, out_path)


def _cmd_init(args, output_dir: str):
    from .init import run_defaults, run_interactive

    if args.defaults:
        run_defaults(output_dir, preset=args.preset)
    else:
        run_interactive(output_dir, preset=args.preset)


def _cmd_list(config: dict):
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


def _cmd_validate(config: dict):
    profiles = config.get("profiles", {})
    if not profiles:
        profiles = {"default": get_profile("default")}
    else:
        profiles = {name: get_profile(name) for name in profiles}
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


def _cmd_doctor():
    from .doctor import print_doctor, run_doctor

    report = run_doctor()
    print_doctor(report)
    sys.exit(1 if report["total_errors"] > 0 else 0)


def _cmd_install_hook(args):
    from .hook import install_hook

    success, msg = install_hook(force=args.force)
    print(msg)
    sys.exit(0 if success else 1)


def _cmd_clean(config: dict, out_path: Path):
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
    for name in _list_profiles(config):
        try:
            prof = get_profile(name)
        except KeyError:
            continue
        tmpl = prof.get("name_template", f"chat-{name}")
        for f in out_path.glob(f"{tmpl}_*.md"):
            f.unlink()
            cleaned += 1
            print(f"  Removed: {f.name}")
        plain = out_path / f"{tmpl}.md"
        if plain.exists():
            plain.unlink()
            cleaned += 1
            print(f"  Removed: {plain.name}")
    # Also clean chat-diff-full files
    for f in out_path.glob("chat-diff-full*.md"):
        f.unlink()
        cleaned += 1
        print(f"  Removed: {f.name}")
    print(f"Cleaned {cleaned} file(s).")


def _cmd_dry_run(config: dict, args):
    profiles_to_run = _collect_profile_names(config, args)
    all_stats = []
    for name in profiles_to_run:
        stats, _ = _run_profile(name, config, args, "", Path("."))
        all_stats.append(stats)
    render_dry_run(all_stats)


def _print_collected(created: list[str]):
    """Print summary of collected output files."""
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


def _cmd_all(config: dict, args, project_name: str, out_path: Path):
    clean_manifest(out_path, "")
    all_created = []
    all_tokens = {}
    for name in _list_profiles(config):
        print(f"[{name}] Collecting...")
        created, tokens_by_file = _run_profile(name, config, args, project_name, out_path)
        if created:
            all_created.extend(created)
            all_tokens.update(tokens_by_file)
            _print_collected(created)
        else:
            print("  No content collected.")

    _write_manifest(out_path, all_created, all_tokens, config)
    all_created.append("chat-manifest.md")
    save_manifest(out_path, all_created)


def _cmd_single(config: dict, args, project_name: str, out_path: Path):
    name = args.profile
    print(f"[{name}] Collecting...")
    created, tokens_by_file = _run_profile(name, config, args, project_name, out_path)
    _print_collected(created)


# ── Watch CLI handlers ─────────────────────────────────────────────


def _cmd_snapshot(argv: list[str]):
    """Handle --snapshot commands.

    Usage:
        arachna --snapshot              list all snapshots
        arachna --snapshot delete <id>  delete a snapshot
        arachna --snapshot --name X     create named snapshot
        arachna --snapshot --profile X  snapshot specific profile
    """
    from .store import delete_snapshot, list_snapshots
    from .watcher import create_snapshot as watch_create_snapshot

    # --snapshot delete <id>
    if "delete" in argv:
        idx = argv.index("delete")
        if idx + 1 < len(argv):
            sid = argv[idx + 1]
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

    # --snapshot with --name
    name = None
    if "--name" in argv:
        idx = argv.index("--name")
        if idx + 1 < len(argv):
            name = argv[idx + 1]
        else:
            print("Error: --name requires a value")
            sys.exit(1)

    # --snapshot with --profile
    profile_name = None
    if "--profile" in argv:
        idx = argv.index("--profile")
        if idx + 1 < len(argv):
            profile_name = argv[idx + 1]
        else:
            print("Error: --profile requires a value")
            sys.exit(1)

    # If --name or --profile given, create snapshot
    if name is not None or profile_name is not None:
        profile = get_profile(profile_name) if profile_name else get_profile("full")
        sid = watch_create_snapshot(profile, name=name)
        file_count = len(load_config().get("profiles", {}))
        print(f"Snapshot '{sid}' created.")
        return

    # --snapshot without arguments → list
    snaps = list_snapshots()
    if not snaps:
        print("No snapshots found.")
        return
    print("Snapshots:")
    for s in snaps:
        name_str = s.get("name") or s["id"]
        created = s.get("created", "?")
        file_count = len(s.get("files", {}))
        print(f"  {s['id']:30} {name_str:20} {created:25} {file_count} files")


def _cmd_diff(argv: list[str]):
    """Handle --diff commands.

    Usage:
        arachna --diff                  diff from HEAD
        arachna --diff --from <id>      diff from specific snapshot
        arachna --diff --profile X      diff for specific profile
        arachna --diff --format xml     XML output
        arachna --diff --full           full context + diff in one output
    """
    from .watcher import compute_diff

    snapshot_id = None
    if "--from" in argv:
        idx = argv.index("--from")
        if idx + 1 < len(argv):
            snapshot_id = argv[idx + 1]
        else:
            print("Error: --from requires a snapshot ID")
            sys.exit(1)

    profile_name = None
    if "--profile" in argv:
        idx = argv.index("--profile")
        if idx + 1 < len(argv):
            profile_name = argv[idx + 1]
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

    # --full flag: full context + diff in single output
    if "--full" in argv:
        # Resolve snapshot ID
        if snapshot_id is None:
            from .store import _store_root

            head_path = _store_root() / "HEAD"
            if not head_path.exists():
                print("Error: No snapshots found. Run 'arachna --snapshot' first.")
                sys.exit(1)
            snapshot_id = head_path.read_text().strip()

        # Get output dir
        output_dir = "."
        if "--output-dir" in argv:
            idx = argv.index("--output-dir")
            if idx + 1 < len(argv):
                output_dir = argv[idx + 1]
        elif "-o" in argv:
            idx = argv.index("-o")
            if idx + 1 < len(argv):
                output_dir = argv[idx + 1]

        config = load_config()
        project_name = config.get("project_name", "Project")
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        # Build fake args for _cmd_diff_full
        class DiffFullArgs:
            verbose = "--verbose" in argv
            compress = "--compress" in argv
            format = fmt
            dry_run = False
            merge = False
            incremental = False
            all = False

        _cmd_diff_full(
            snapshot_id,
            profile_name,
            config,
            DiffFullArgs(),
            project_name,
            out_path,
        )
        return

    # Resolve snapshot ID
    if snapshot_id is None:
        from .store import _store_root

        head_path = _store_root() / "HEAD"
        if not head_path.exists():
            print("Error: No snapshots found. Run 'arachna --snapshot' first.")
            sys.exit(1)
        snapshot_id = head_path.read_text().strip()

    profile = get_profile(profile_name) if profile_name else get_profile("full")
    sections = compute_diff(snapshot_id, profile, fmt=fmt)

    if not sections:
        print("No changes since snapshot.")
        return

    # Print to stdout (same format as collected context)
    for section in sections:
        print(section.content)


def _cmd_store(argv: list[str]):
    """Handle --store commands.

    Usage:
        arachna --store gc      garbage collect unreferenced objects
        arachna --store stats   show store statistics
    """
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


if __name__ == "__main__":
    main()
