# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""CLI handlers for 'arachna plugins' command."""

import sys

from ..plugins.plugins import install_plugin, list_plugins, uninstall_plugin
from . import register


@register("plugins-list")
def _cmd_plugins_list(args, config: dict):
    plugins = list_plugins()
    if not plugins:
        print("No plugins available.")
        return

    print("Plugins:")
    for name, info in sorted(plugins.items()):
        status = "installed" if info["installed"] else "not installed"
        deps = ", ".join(info["deps"])
        print(f"  {name:15} {status:15} ({deps})")


@register("plugins-install")
def _cmd_plugins_install(args, config: dict):
    result = install_plugin(args.language, execute=args.execute)
    print(result)


@register("plugins-uninstall")
def _cmd_plugins_uninstall(args, config: dict):
    result = uninstall_plugin(args.language)
    print(result)


_PLUGINS_HANDLERS = {
    "list": _cmd_plugins_list,
    "install": _cmd_plugins_install,
    "uninstall": _cmd_plugins_uninstall,
}


def _dispatch_plugins(args, config: dict, parser):
    plugins_cmd = getattr(args, "plugins_command", None)
    handler = _PLUGINS_HANDLERS.get(plugins_cmd)
    if handler:
        handler(args, config)
    else:
        plugins_p = None
        for action in parser._actions:
            if action.dest == "command" and hasattr(action, "choices"):
                choices = action.choices
                if "plugins" in choices:
                    plugins_p = choices["plugins"]
                    break
        if plugins_p:
            plugins_p.print_help()
        sys.exit(1)
