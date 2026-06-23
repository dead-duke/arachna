"""CLI handlers for 'arachna collect' command."""

import json
import subprocess
import sys

from ..config.core.config import get_profile
from ..config.core.validator import validate_profile
from ..config.profile_config import ArachnaConfig, ProfileConfig
from ..config.urls import validate_remote_url
from ..domain.collection.collector import (
    _MANIFEST,
    clean_manifest,
    collect,
    load_manifest,
    save_manifest,
)
from ..domain.collection.gatherer import dry_run
from ..domain.path_utils import SafePath
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


def _cfg_project_name(config: ArachnaConfig) -> str:
    return config.project_name


def _cfg_get_profile(name: str, root, config: ArachnaConfig) -> ProfileConfig:
    return get_profile(name, root=root, config=config)


def _resolve_profiles(config: ArachnaConfig, root):
    profiles = config.profiles
    if not profiles:
        return {"default": get_profile("default", root=root)}, 0
    valid_profiles = {}
    error_count = 0
    for name in profiles:
        try:
            valid_profiles[name] = get_profile(name, root=root, config=config)
        except KeyError as e:
            print(f"  Error: profile '{name}': {e}")
            error_count += 1
    return valid_profiles, error_count


def _collect_one_profile(name, profile, args, out_path, root, project_name, skip_clean=False):
    profile = apply_args_to_profile(profile, args)
    if getattr(args, "no_pre_commands", False):
        profile.pre_commands = []

    if args.dry_run:
        query = getattr(args, "query", None)
        mode = getattr(args, "mode", "full")
        stats = dry_run(profile, root=root, query=query, mode=mode)
        stats["name"] = name
        return None, None, stats

    name_tmpl = profile.name_template
    if not args.merge and not skip_clean:
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


def _aggregate_results(created, tokens_by_file, all_created, all_tokens):
    if created:
        all_created.extend(created)
        if tokens_by_file:
            all_tokens.update(tokens_by_file)
        print_collected(created)
    else:
        print("  No content collected.")


def _update_manifest(out_path, created, name_tmpl, merge):
    prev = load_manifest(out_path)
    if merge:
        updated = list(prev)
        for f in created:
            if f not in updated:
                updated.append(f)
    else:
        updated = [f for f in prev if not f.startswith(name_tmpl)]
        updated.extend(created)
    save_manifest(out_path, updated)


@register("collect-profile")
def _cmd_collect_profile(args, config: ArachnaConfig):
    root = get_root(config)
    project_name = _cfg_project_name(config)
    out_path = SafePath(root / parse_output_dir(args, config), root)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"[{args.profile}] Collecting...")
    try:
        profile = _cfg_get_profile(args.profile, root, config)
    except KeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    created, _, dry_run_stats = _collect_one_profile(
        args.profile, profile, args, out_path, root, project_name
    )
    if args.dry_run:
        if dry_run_stats:
            render_dry_run([dry_run_stats])
        return

    _update_manifest(out_path, created, profile.name_template, args.merge)
    print_collected(created)


@register("collect-all")
def _cmd_collect_all(args, config: ArachnaConfig):
    root = get_root(config)
    project_name = _cfg_project_name(config)
    out_path = SafePath(root / parse_output_dir(args, config), root)
    out_path.mkdir(parents=True, exist_ok=True)

    clean_manifest(out_path, "")
    all_created, all_tokens, all_dry_run_stats = [], {}, []

    for name in list_profiles(config):
        print(f"[{name}] Collecting...")
        try:
            profile = _cfg_get_profile(name, root, config)
        except KeyError:
            continue

        created, tokens_by_file, dry_run_stats = _collect_one_profile(
            name, profile, args, out_path, root, project_name, skip_clean=True
        )
        if args.dry_run:
            if dry_run_stats:
                all_dry_run_stats.append(dry_run_stats)
            continue
        _aggregate_results(created, tokens_by_file, all_created, all_tokens)

    if args.dry_run:
        if all_dry_run_stats:
            render_dry_run(all_dry_run_stats)
        return

    if all_created:
        write_manifest(out_path, all_created, all_tokens, config)
        all_created.append("chat-manifest.md")
        save_manifest(out_path, all_created)


@register("collect-list")
def _cmd_collect_list(args, config: ArachnaConfig):
    root = get_root(config)
    for name in list_profiles(config):
        try:
            prof = _cfg_get_profile(name, root, config)
        except KeyError:
            print(f"  Warning: profile '{name}' not found, skipping")
            continue
        if prof.command:
            print(f"  {name}: command ({prof.max_tokens} tokens)")
        else:
            print(
                f"  {name}: {len(prof.directories)} dirs, {len(prof.files)} files ({prof.max_tokens} tokens)"
            )


def _validate_and_print(profiles):
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
def _cmd_collect_validate(args, config: ArachnaConfig):
    root = get_root(config)
    profiles, resolve_errors = _resolve_profiles(config, root)
    all_errors = _validate_and_print(profiles)[0] + resolve_errors
    all_warnings = _validate_and_print(profiles)[1]
    print(f"\nResult: {all_errors} error(s), {all_warnings} warning(s)")
    sys.exit(1 if all_errors > 0 else 0)


@register("collect-clean")
def _cmd_collect_clean(args, config: ArachnaConfig):
    root = get_root(config)
    out_path = SafePath(root / parse_output_dir(args, config), root)
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


def _cmd_collect_repo(args, config: ArachnaConfig):
    root = get_root(config)
    try:
        validate_remote_url(args.repo)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    url = args.repo
    print(f"Cloning {url}...")
    try:
        from ..config.remote import collect_remote

        print(
            collect_remote(
                url=url,
                root=root,
                profile=args.profile or "full",
                output_dir=parse_output_dir(args, config),
            )
        )
    except (OSError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"Error: {e}")
        sys.exit(1)
