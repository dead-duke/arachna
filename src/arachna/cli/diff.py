"""CLI handlers for 'arachna diff' command."""

import sys
from pathlib import Path

from ..config.core.config import get_profile
from ..config.profile_config import ArachnaConfig, ProfileConfig
from ..domain.collection.collector import (
    _write_diff_parts,
    clean_manifest,
    collect,
    load_manifest,
    save_manifest,
)
from ..domain.differ_stats import compute_diff_stats
from ..domain.path_utils import SafePath
from ..domain.tokenization.tokenizer import count_tokens, load_tokenizer
from ..snapshot.snapshots import compute_diff
from ..snapshot.store.store import list_snapshots, load_snapshot
from . import register
from ._helpers import get_root, parse_output_dir, print_collected


@register("diff-all")
def _cmd_diff_all(args, config: ArachnaConfig | dict):
    root = get_root(config)
    project_name = (
        config.project_name
        if isinstance(config, ArachnaConfig)
        else config.get("project_name", "Project")
    )
    output_dir = parse_output_dir(args, config)
    out_path = SafePath(root / output_dir, root)
    out_path.mkdir(parents=True, exist_ok=True)
    profile_name = args.profile or "full"
    try:
        profile = get_profile(
            profile_name, root=root, config=config if isinstance(config, ArachnaConfig) else None
        )
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)
    if args.compress:
        profile.compress = True
    name_tmpl = "chat-diff-all"
    clean_manifest(out_path, name_tmpl)
    created, _, _parts, _metrics = collect(
        profile,
        project_name,
        str(out_path),
        root=root,
        verbose=False,
        incremental=False,
        merge=False,
        query=args.query,
        mode=args.mode or "full",
        name_template=name_tmpl,
    )
    if created:
        print_collected(created)
        prev = load_manifest(out_path)
        updated = [f for f in prev if not f.startswith("chat-diff-all")]
        updated.extend(created)
        save_manifest(out_path, updated)
    else:
        print("  No content collected.")


def _validate_diff_args(args) -> None:
    if args.all and args.from_snapshot:
        print("Error: Cannot use --all and --from together.")
        sys.exit(1)


def _resolve_snapshot_id(args, root: Path) -> str:
    if args.from_snapshot:
        return args.from_snapshot
    snaps = list_snapshots(root=root)
    if len(snaps) == 0:
        print("Error: No snapshots found.")
        sys.exit(1)
    elif len(snaps) == 1:
        return snaps[0]["id"]
    else:
        print("Error: Multiple snapshots found. Use --from to specify which one:")
        for s in snaps:
            print(f"  arachna diff --from {s['id']:20} # {s.get('name', s['id'])}")
        sys.exit(1)


def _resolve_diff_profile(args, snapshot_id, root, config):
    if args.profile:
        try:
            return get_profile(
                args.profile,
                root=root,
                config=config if isinstance(config, ArachnaConfig) else None,
            )
        except KeyError as e:
            print(f"Error: {e}")
            sys.exit(1)
    manifest = load_snapshot(snapshot_id, root=root)
    stored = manifest.get("profile", {})
    if isinstance(stored, dict):
        defaults = ProfileConfig()
        return ProfileConfig(
            name_template=stored.get("name_template", defaults.name_template),
            title_template=stored.get("title_template", defaults.title_template),
            max_tokens=stored.get("max_tokens", defaults.max_tokens),
            split_mode=stored.get("split_mode", defaults.split_mode),
            directories=stored.get("directories", defaults.directories),
            patterns=stored.get("patterns", defaults.patterns),
            files=stored.get("files", defaults.files),
            exclude_patterns=stored.get("exclude_patterns", defaults.exclude_patterns),
            pre_commands=stored.get("pre_commands", defaults.pre_commands),
            post_commands=stored.get("post_commands", defaults.post_commands),
            command=stored.get("command"),
            compress=stored.get("compress", defaults.compress),
            use_gitignore=stored.get("use_gitignore", defaults.use_gitignore),
        )
    print(f"Error: Snapshot '{snapshot_id}' has legacy format. Use --profile.")
    sys.exit(1)


def _apply_diff_mode(args, sections, snapshot_id, to_snapshot_id, root):
    if args.mode == "structural":
        from ..snapshot.diff.differ_structural import structural_diff_sections

        return structural_diff_sections(sections, args.format or "markdown")
    elif args.mode == "repo-map":
        from ..snapshot.snapshots import apply_repo_map_to_sections

        return apply_repo_map_to_sections(sections, snapshot_id, to_snapshot_id, root=root)
    return sections


def _write_diff_output(sections, snapshot_id, to_snapshot_id, profile, config, args):
    output_dir = parse_output_dir(args, config)
    project_name = (
        config.project_name
        if isinstance(config, ArachnaConfig)
        else config.get("project_name", "Project")
    )
    root = get_root(config)
    out_path = SafePath(root / output_dir, root)
    out_path.mkdir(parents=True, exist_ok=True)
    max_tokens = profile.max_tokens
    tokenizer_spec = profile.tokenizer
    tokenizer = load_tokenizer(tokenizer_spec) if tokenizer_spec != "default" else count_tokens
    if to_snapshot_id:
        name_tmpl = f"chat-diff-{snapshot_id}-to-{to_snapshot_id}"
        title_tmpl = f"# {project_name} — DIFF from {snapshot_id} to {to_snapshot_id} (part {{part}} of {{total}})\n\n"
    else:
        name_tmpl = f"chat-diff-{snapshot_id}"
        title_tmpl = f"# {project_name} — DIFF from {snapshot_id} (part {{part}} of {{total}})\n\n"
    clean_manifest(out_path, name_tmpl)
    created = _write_diff_parts(
        sections, out_path, name_tmpl, title_tmpl, project_name, max_tokens, tokenizer
    )
    print_collected(created)
    prev = load_manifest(out_path)
    updated = [f for f in prev if not f.startswith(name_tmpl)]
    updated.extend(created)
    save_manifest(out_path, updated)


def _output_diff_results(args, sections, snapshot_id, to_snapshot_id, profile, config) -> bool:
    if args.stat:
        stats = compute_diff_stats(sections)
        print(f"Modified: {stats['modified']}")
        print(f"Added:    {stats['added']}")
        print(f"Deleted:  {stats['deleted']}")
        if stats["renamed"]:
            print(f"Renamed:  {stats['renamed']}")
        if stats["moved"]:
            print(f"Moved:    {stats['moved']}")
        print(f"Tokens:   {stats['tokens']}")
        return True
    if not sections:
        print("No changes since snapshot.")
        return True
    content_sections = [s for s in sections if s.content.strip()]
    if not content_sections:
        print("No changes since snapshot.")
        return True
    _write_diff_output(content_sections, snapshot_id, to_snapshot_id, profile, config, args)
    return False


@register("diff")
def _cmd_diff(args, config: ArachnaConfig | dict):
    _validate_diff_args(args)
    if args.all:
        _cmd_diff_all(args, config)
        return
    root = get_root(config)
    snapshot_id = _resolve_snapshot_id(args, root)
    to_snapshot_id = args.to
    profile = _resolve_diff_profile(args, snapshot_id, root, config)
    fmt = args.format or "markdown"
    line_numbers = getattr(args, "line_numbers", False)
    if args.compress:
        profile.compress = True
    sections = compute_diff(
        snapshot_id,
        profile,
        root=root,
        fmt=fmt,
        to_snapshot_id=to_snapshot_id,
        flat=args.flat,
        line_numbers=line_numbers,
    )
    sections = _apply_diff_mode(args, sections, snapshot_id, to_snapshot_id, root)
    if _output_diff_results(args, sections, snapshot_id, to_snapshot_id, profile, config):
        return
