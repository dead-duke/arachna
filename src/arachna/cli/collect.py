# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna collect' command."""

import json
import sys
from pathlib import Path

from ..collector import _MANIFEST, clean_manifest, collect, load_manifest, save_manifest
from ..config import get_profile
from ..gatherer import dry_run
from ..renderer import render_dry_run
from ..validator import validate_profile
from . import register
from ._helpers import (
    apply_args_to_profile,
    list_profiles,
    parse_output_dir,
    print_collected,
    write_manifest,
)


def _get_root(config: dict) -> Path:
    return Path(config.get("_root", Path.cwd()))


@register("collect-profile")
def _cmd_collect_profile(args, config: dict):
    root = _get_root(config)
    project_name = config.get("project_name", "Project")
    output_dir = parse_output_dir(args, config)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"[{args.profile}] Collecting...")
    try:
        profile = get_profile(args.profile, root=root, config=config)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    profile = apply_args_to_profile(profile, args)

    if getattr(args, "no_pre_commands", False):
        profile["pre_commands"] = []

    if args.dry_run:
        query = getattr(args, "query", None)
        mode = getattr(args, "mode", "full")
        stats = dry_run(profile, root=root, query=query, mode=mode)
        stats["name"] = args.profile
        render_dry_run([stats])
        return

    name_tmpl = profile.get("name_template", f"chat-{args.profile}")

    if not args.merge:
        clean_manifest(out_path, name_tmpl)

    created, tokens_by_file, _parts, _metrics = collect(
        profile,
        project_name,
        str(out_path),
        root=root,
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

    print_collected(created)


@register("collect-all")
def _cmd_collect_all(args, config: dict):
    root = _get_root(config)
    project_name = config.get("project_name", "Project")
    output_dir = parse_output_dir(args, config)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    clean_manifest(out_path, "")
    all_created = []
    all_tokens = {}
    for name in list_profiles(config):
        print(f"[{name}] Collecting...")
        try:
            profile = get_profile(name, root=root, config=config)
        except KeyError:
            continue
        profile = apply_args_to_profile(profile, args)

        if getattr(args, "no_pre_commands", False):
            profile["pre_commands"] = []

        if args.dry_run:
            query = getattr(args, "query", None)
            mode = getattr(args, "mode", "full")
            stats = dry_run(profile, root=root, query=query, mode=mode)
            stats["name"] = name
            all_created_stats = getattr(args, "_all_stats", None)
            if all_created_stats is None:
                all_created_stats = []
                args._all_stats = all_created_stats
            all_created_stats.append(stats)
            continue

        name_tmpl = profile.get("name_template", f"chat-{name}")
        clean_manifest(out_path, name_tmpl)

        created, tokens_by_file, _parts, _metrics = collect(
            profile,
            project_name,
            str(out_path),
            root=root,
            verbose=args.verbose,
            incremental=args.incremental,
            merge=False,
            query=getattr(args, "query", None),
            mode=getattr(args, "mode", "full"),
        )

        if created:
            all_created.extend(created)
            all_tokens.update(tokens_by_file)
            print_collected(created)
        else:
            print("  No content collected.")

    if args.dry_run:
        all_stats = getattr(args, "_all_stats", [])
        if all_stats:
            render_dry_run(all_stats)
        return

    if all_created:
        write_manifest(out_path, all_created, all_tokens, config)
        all_created.append("chat-manifest.md")
        save_manifest(out_path, all_created)


@register("collect-list")
def _cmd_collect_list(args, config: dict):
    root = _get_root(config)
    for name in list_profiles(config):
        try:
            prof = get_profile(name, root=root, config=config)
        except KeyError:
            print(f"  Warning: profile '{name}' not found, skipping")
            continue
        cmd = prof.get("command")
        if cmd:
            print(f"  {name}: command ({prof.get('max_tokens', '?')} tokens)")
        else:
            dirs = len(prof.get("directories", []))
            files = len(prof.get("files", []))
            print(f"  {name}: {dirs} dirs, {files} files ({prof.get('max_tokens', '?')} tokens)")


@register("collect-validate")
def _cmd_collect_validate(args, config: dict):
    root = _get_root(config)
    profiles = config.get("profiles", {})
    if not profiles:
        profiles = {"default": get_profile("default", root=root, config=config)}
    else:
        valid_profiles = {}
        for name in profiles:
            try:
                valid_profiles[name] = get_profile(name, root=root, config=config)
            except KeyError as e:
                print(f"  Warning: profile '{name}': {e}")
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


@register("collect-clean")
def _cmd_collect_clean(args, config: dict):
    root = _get_root(config)
    output_dir = parse_output_dir(args, config)
    out_path = root / output_dir
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
