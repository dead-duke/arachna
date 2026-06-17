# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Shell completion for bash and zsh — argparse subparsers."""

import sys


def generate_bash():
    """Generate bash completion script with subcommand support."""
    script = """
_arachna_complete() {
    local cur prev words cword
    _init_completion || return

    local commands="collect snapshot diff store plugins presets profile doctor init manifest completion"

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands --version --help" -- "$cur"))
        return
    fi

    local cmd="${words[1]}"
    case $cmd in
        collect)
            case $prev in
                -p|--profile|--mode|--format|--output-dir|-o|--query|--repo)
                    return
                    ;;
            esac
            COMPREPLY=($(compgen -W "--profile --all --list --validate --clean --dry-run --output-dir --verbose --compress --incremental --format --merge --query --no-pre-commands --mode --repo -p -a -c -l -o -v" -- "$cur"))
            ;;
        snapshot)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "create list update delete info rename" -- "$cur"))
            else
                local sub="${words[2]}"
                case $sub in
                    create)
                        COMPREPLY=($(compgen -W "--profile --name -p" -- "$cur"))
                        ;;
                    update|delete|info)
                        COMPREPLY=($(compgen -W "--profile -p" -- "$cur"))
                        ;;
                esac
            fi
            ;;
        diff)
            case $prev in
                --from|--to|--profile|-p|--format|--mode|--output-dir|-o|--query)
                    return
                    ;;
            esac
            COMPREPLY=($(compgen -W "--from --to --all --profile --stat --flat --format --mode --compress --output-dir --query -p -o" -- "$cur"))
            ;;
        store)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "stats gc" -- "$cur"))
            fi
            ;;
        plugins)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "list install uninstall" -- "$cur"))
            else
                local sub="${words[2]}"
                case $sub in
                    install|uninstall)
                        COMPREPLY=($(compgen -W "javascript typescript go tiktoken" -- "$cur"))
                        ;;
                    install)
                        COMPREPLY=($(compgen -W "--execute" -- "$cur"))
                        ;;
                esac
            fi
            ;;
        presets)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "update" -- "$cur"))
            else
                COMPREPLY=($(compgen -W "--url" -- "$cur"))
            fi
            ;;
        profile)
            COMPREPLY=($(compgen -W "--profile --format --output-dir -p -o" -- "$cur"))
            ;;
        init)
            COMPREPLY=($(compgen -W "--defaults --preset --install-hook --force --output-dir -o" -- "$cur"))
            ;;
        completion)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "bash zsh" -- "$cur"))
            fi
            ;;
        manifest)
            COMPREPLY=($(compgen -W "--json --output-dir -o" -- "$cur"))
            ;;
        doctor)
            ;;
        *)
            COMPREPLY=($(compgen -W "$commands --version --help" -- "$cur"))
            ;;
    esac
}
complete -F _arachna_complete arachna
"""
    print(script.strip())


def generate_zsh():
    """Generate zsh completion script with subcommand support."""
    script = """
#compdef arachna

_arachna_collect() {
    _arguments -s \\
        '--profile[Profile name to collect]:profile:' \\
        '-p[Profile name to collect]:profile:' \\
        '--all[Collect all profiles]' \\
        '-a[Collect all profiles]' \\
        '--list[List available profiles]' \\
        '-l[List available profiles]' \\
        '--validate[Validate config for errors]' \\
        '--clean[Remove all collected files]' \\
        '-c[Remove all collected files]' \\
        '--dry-run[Preview without writing]' \\
        '--output-dir[Override output directory]:dir:_files -/' \\
        '-o[Override output directory]:dir:_files -/' \\
        '--verbose[Show skipped files]' \\
        '-v[Show skipped files]' \\
        '--compress[Compress whitespace]' \\
        '--incremental[Only changed files]' \\
        '--format[Output format]:format:(markdown xml json)' \\
        '--merge[Append to existing output]' \\
        '--query[Filter files by query]:query:' \\
        '--no-pre-commands[Skip pre_commands]' \\
        '--mode[Collection mode]:mode:(full headers repo-map)' \\
        '--repo[Remote repository URL]:url:'
}

_arachna_snapshot() {
    local -a subcmds
    subcmds=(
        'create:Create a named snapshot'
        'list:List all snapshots'
        'update:Update an existing snapshot'
        'delete:Delete a snapshot'
        'info:Show snapshot details'
        'rename:Rename a snapshot'
    )
    _describe 'command' subcmds
}

_arachna_diff() {
    _arguments -s \\
        '--from[Source snapshot ID]:id:' \\
        '--to[Target snapshot ID]:id:' \\
        '--all[Full project as diff]' \\
        '--profile[Profile name]:profile:' \\
        '-p[Profile name]:profile:' \\
        '--stat[Stats only]' \\
        '--flat[Flat output]' \\
        '--format[Output format]:format:(markdown xml json)' \\
        '--mode[Diff mode]:mode:(full structural repo-map)' \\
        '--compress[Compress whitespace]' \\
        '--output-dir[Override output directory]:dir:_files -/' \\
        '-o[Override output directory]:dir:_files -/' \\
        '--query[Filter files by query]:query:'
}

_arachna_store() {
    local -a subcmds
    subcmds=(
        'stats:Show store statistics'
        'gc:Garbage collect store'
    )
    _describe 'command' subcmds
}

_arachna_plugins() {
    local -a subcmds
    subcmds=(
        'list:List plugins'
        'install:Install plugin'
        'uninstall:Uninstall plugin'
    )
    _describe 'command' subcmds
}

_arachna_presets() {
    _arguments -s \\
        '1: :->cmd' \\
        '*:: :->args'
    case $state in
        cmd)
            _alternative 'command:command:(update)'
            ;;
        args)
            _arguments '--url[Remote presets URL]:url:'
            ;;
    esac
}

_arachna_profile() {
    _arguments -s \\
        '--profile[Profile name]:profile:' \\
        '-p[Profile name]:profile:' \\
        '--format[Output format]:format:(terminal json)' \\
        '--output-dir[Override output directory]:dir:_files -/' \\
        '-o[Override output directory]:dir:_files -/'
}

_arachna_init() {
    _arguments -s \\
        '--defaults[Use defaults]' \\
        '--preset[Use specific preset]:preset:' \\
        '--install-hook[Install post-commit git hook]' \\
        '--force[Force overwrite]' \\
        '--output-dir[Override output directory]:dir:_files -/' \\
        '-o[Override output directory]:dir:_files -/'
}

_arachna_manifest() {
    _arguments -s \\
        '--json[Machine-readable JSON]' \\
        '--output-dir[Override output directory]:dir:_files -/' \\
        '-o[Override output directory]:dir:_files -/'
}

_arachna_completion() {
    _arguments -s \\
        '1:shell:(bash zsh)'
}

_arachna() {
    local -a commands
    commands=(
        'collect:Collect project context'
        'snapshot:Manage snapshots'
        'diff:Diff from snapshot'
        'store:Store management'
        'plugins:Plugin management'
        'presets:Preset management'
        'profile:Profile project'
        'doctor:Run configuration diagnostic'
        'init:Create .arachna.json interactively'
        'manifest:Show collected files manifest'
        'completion:Generate shell completion'
    )

    _arguments -s \\
        '--version[Show version]' \\
        '--help[Show help]' \\
        '1: :->cmd' \\
        '*:: :->args'

    case $state in
        cmd)
            _describe 'command' commands
            ;;
        args)
            local cmd=$words[1]
            case $cmd in
                collect) _arachna_collect ;;
                snapshot) _arachna_snapshot ;;
                diff) _arachna_diff ;;
                store) _arachna_store ;;
                plugins) _arachna_plugins ;;
                presets) _arachna_presets ;;
                profile) _arachna_profile ;;
                init) _arachna_init ;;
                manifest) _arachna_manifest ;;
                completion) _arachna_completion ;;
            esac
            ;;
    esac
}
_arachna
"""
    print(script.strip())


def main():
    shell = sys.argv[1] if len(sys.argv) > 1 else ""
    if shell == "bash":
        generate_bash()
    elif shell == "zsh":
        generate_zsh()
    else:
        print("Usage: arachna completion bash|zsh")
        print("  source <(arachna completion bash)")
        print("  source <(arachna completion zsh)")


if __name__ == "__main__":
    main()
