# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Shell completion for bash and zsh."""

import sys


def generate_bash():
    """Generate bash completion script."""
    script = """
_arachna_complete() {
    local cur prev words cword
    _init_completion || return

    case $prev in
        -p|--profile)
            COMPREPLY=()
            return
            ;;
        -o|--output-dir)
            COMPREPLY=($(compgen -d -- "$cur"))
            return
            ;;
        --format)
            COMPREPLY=($(compgen -W "markdown xml json" -- "$cur"))
            return
            ;;
    esac

    if [[ $cur == -* ]]; then
        COMPREPLY=($(compgen -W "--profile --all --clean --list --validate --init --dry-run --output-dir --verbose --compress --incremental --format --defaults --merge --force --preset --install-hook --doctor --help --version -p -a -c -l -o -v" -- "$cur"))
    fi
}
complete -F _arachna_complete arachna
"""
    print(script.strip())


def generate_zsh():
    """Generate zsh completion script."""
    script = """
#compdef arachna

_arachna() {
    local -a commands
    commands=(
        '--profile[Collect specific profile]:profile:'
        '--all[Collect all profiles]'
        '--clean[Remove all collected files]'
        '--list[List available profiles]'
        '--validate[Validate config]'
        '--init[Create config interactively]'
        '--dry-run[Preview without writing]'
        '--output-dir[Override output directory]:dir:_files -/'
        '--verbose[Show skipped files]'
        '--compress[Compress whitespace]'
        '--incremental[Only changed files]'
        '--format[Output format]:format:(markdown xml json)'
        '--defaults[Use defaults with --init]'
        '--merge[Append to existing output]'
        '--force[Force overwrite with --install-hook]'
        '--preset[Use specific preset with --init]:preset:'
        '--install-hook[Install post-commit git hook]'
        '--doctor[Run configuration diagnostic]'
        '--help[Show help]'
        '--version[Show version]'
    )

    _arguments -s $commands
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
