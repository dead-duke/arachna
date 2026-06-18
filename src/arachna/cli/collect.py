# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna collect' command."""

import json
import sys
from pathlib import Path

from ..config.config import get_profile
from ..config.validator import validate_profile
from ..domain.collector import _MANIFEST, clean_manifest, collect, load_manifest, save_manifest
from ..domain.gatherer import dry_run
from . import register
from ._helpers import (
    apply_args_to_profile,
    get_root,
    list_profiles,
    parse_output_dir,
    print_collected,
    write_manifest,
)
from .renderer import render_dry_run


def _collect_one_profile(name, profile, args, out_path, root, project_name):
    """Collect a single profile. Returns (created, tokens_by_file) or (None, dry_run_stats)."""
    profile = apply_args_to_profile(profile, args)
    if getattr(args, "no_pre_commands", False):
        profile["pre_commands"] = []

    if args.dry_run:
        query = getattr(args, "query", None)
        mode = getattr(args, "mode", "full")
        stats = dry_run(profile, root=root, query=query, mode=mode)
        stats["name"] = name
        return None, None, stats

    name_tmpl = profile.get("name_template", f"chat-{name}")
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
    return created, tokens_by_file, None


def _process_collect_results(created, tokens_by_file, all_created, all_tokens):
    """Aggregate collection results into running totals."""
    if created:
        all_created.extend(created)
        if tokens_by_file:
            all_tokens.update(tokens_by_file)
        print_collected(created)
    else:
        print("  No content collected.")


@register("collect-profile")
def _cmd_collect_profile(args, config: dict):
    root = get_root(config)
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

    created, tokens_by_file, dry_run_stats = _collect_one_profile(
        args.profile, profile, args, out_path, root, project_name
    )
    if args.dry_run:
        if dry_run_stats:
            render_dry_run([dry_run_stats])
        return

    prev = load_manifest(out_path)
    name_tmpl = profile.get("name_template", f"chat-{args.profile}")
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
    root = get_root(config)
    project_name = config.get("project_name", "Project")
    output_dir = parse_output_dir(args, config)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    clean_manifest(out_path, "")
    all_created = []
    all_tokens = {}
    all_dry_run_stats = []
    for name in list_profiles(config):
        print(f"[{name}] Collecting...")
        try:
            profile = get_profile(name, root=root, config=config)
        except KeyError:
            continue

        created, tokens_by_file, dry_run_stats = _collect_one_profile(
            name, profile, args, out_path, root, project_name
        )
        if args.dry_run:
            if dry_run_stats:
                all_dry_run_stats.append(dry_run_stats)
            continue

        _process_collect_results(created, tokens_by_file, all_created, all_tokens)

    if args.dry_run:
        if all_dry_run_stats:
            render_dry_run(all_dry_run_stats)
        return

    if all_created:
        write_manifest(out_path, all_created, all_tokens, config)
        all_created.append("chat-manifest.md")
        save_manifest(out_path, all_created)


@register("collect-list")
def _cmd_collect_list(args, config: dict):
    root = get_root(config)
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


def _resolve_profiles(config, root):
    """Build valid profiles dict from config."""
    profiles = config.get("profiles", {})
    if not profiles:
        return {"default": get_profile("default", root=root, config=config)}
    valid_profiles = {}
    for name in profiles:
        try:
            valid_profiles[name] = get_profile(name, root=root, config=config)
        except KeyError as e:
            print(f"  Warning: profile '{name}': {e}")
    return valid_profiles


def _validate_and_print(profiles):
    """Validate profiles and print results. Returns (errors, warnings) counts."""
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
    return all_errors, all_warnings


@register("collect-validate")
def _cmd_collect_validate(args, config: dict):
    root = get_root(config)
    profiles = _resolve_profiles(config, root)
    all_errors, all_warnings = _validate_and_print(profiles)
    print(f"\nResult: {all_errors} error(s), {all_warnings} warning(s)")
    sys.exit(1 if all_errors > 0 else 0)


@register("collect-clean")
def _cmd_collect_clean(args, config: dict):
    root = get_root(config)
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


def _cmd_collect_repo(args, config: dict):
    """Handle arachna collect --repo <url>."""
    url = args.repo
    if not url.startswith(("http://", "https://")):
        print("Error: only http:// and https:// URLs are allowed.")
        print(f"  Got: {url}")
        sys.exit(1)

    profile = args.profile or "full"
    output_dir = parse_output_dir(args, config)
    root = get_root(config)

    print(f"Cloning {url}...")
    try:
        from ..config.remote import collect_remote

        result = collect_remote(
            url=url,
            profile=profile,
            output_dir=output_dir,
            root=root,
        )
        print(result)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
