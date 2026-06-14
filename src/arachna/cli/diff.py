# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna diff' command."""

import sys
from pathlib import Path

from ..collector import _write_diff_parts, clean_manifest, collect, load_manifest, save_manifest
from ..config import get_profile
from ..differ import compute_diff_stats
from ..store import list_snapshots, load_snapshot
from ..tokenizer import count_tokens, load_tokenizer
from ..watcher import compute_diff
from . import register
from ._helpers import parse_output_dir, print_collected


def _get_root(config: dict) -> Path | None:
    root_str = config.get("_root")
    return Path(root_str) if root_str else None


@register("diff")
def _cmd_diff(args, config: dict):
    if args.all and args.from_snapshot:
        print("Error: Cannot use --all and --from together.")
        print("  arachna diff --all         full project as diff (no snapshot)")
        print("  arachna diff --from <id>   diff from a specific snapshot")
        sys.exit(1)

    if args.all:
        _cmd_diff_all(args, config)
        return

    root = _get_root(config)
    snapshot_id = args.from_snapshot
    to_snapshot_id = args.to

    profile = None
    if args.profile:
        try:
            profile = get_profile(args.profile, config=config)
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)

    fmt = args.format or "markdown"
    stat_only = args.stat
    flat_mode = args.flat
    diff_mode = args.mode or "full"

    if snapshot_id is None:
        snaps = list_snapshots(root=root)
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

    output_dir = parse_output_dir(args, config)
    project_name = config.get("project_name", "Project")
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if profile is None:
        manifest = load_snapshot(snapshot_id, root=root)
        stored = manifest.get("profile", {})
        if isinstance(stored, dict):
            profile = stored
        else:
            print(f"Error: Snapshot '{snapshot_id}' has legacy format. Use --profile.")
            sys.exit(1)

    if args.compress:
        profile["compress"] = True

    sections = compute_diff(
        snapshot_id, profile, fmt=fmt, to_snapshot_id=to_snapshot_id, flat=flat_mode, root=root
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
        from ..differ_structural import structural_diff_sections

        sections = structural_diff_sections(sections, fmt)
    elif diff_mode == "repo-map":
        from ..gatherer import _apply_repo_map_to_sections

        sections = _apply_repo_map_to_sections(
            sections, snapshot_id, to_snapshot_id, profile, root=root
        )

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
    print_collected(created)
    prev = load_manifest(out_path)
    updated = [f for f in prev if not f.startswith(name_tmpl)]
    updated.extend(created)
    save_manifest(out_path, updated)


@register("diff-all")
def _cmd_diff_all(args, config: dict):
    root = _get_root(config)
    project_name = config.get("project_name", "Project")
    output_dir = parse_output_dir(args, config)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    profile_name = args.profile or "full"
    diff_mode = args.mode or "full"
    query = args.query
    compress = args.compress

    try:
        profile = get_profile(profile_name, config=config)
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
        root=root,
    )

    if created:
        print_collected(created)
        prev = load_manifest(out_path)
        updated = [f for f in prev if not f.startswith("chat-diff-all")]
        updated.extend(created)
        save_manifest(out_path, updated)
    else:
        print("  No content collected.")
