# arachna

[![PyPI version](https://img.shields.io/pypi/v/arachna)](https://pypi.org/project/arachna/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Context collector for AI — gathers project files into token-limited chunks.

## What is arachna

arachna is a command-line tool that collects your project's source code and documentation into files ready to be sent to an AI. It understands tokens (not lines) and splits output smartly so nothing gets cut in the middle.

## Why arachna

- Token-aware splitting: other tools split by lines, arachna splits by tokens
- Zero dependencies: just Python stdlib
- Uniformly packed parts: all output chunks are filled densely to the token limit
- Multiple presets: 17 language and engine presets out of the box
- Smart defaults: arachna --init detects your project in seconds

## Install

    pip install arachna

## Quick start

    cd your-project
    arachna --init
    arachna --all

Creates arachna_context/ folder with .md files ready for AI.

## Commands

    arachna --init              interactive setup
    arachna --init --defaults   auto-detect everything
    arachna --init --preset X   use specific preset
    arachna --all               collect all profiles
    arachna --profile code      collect one profile
    arachna --all --dry-run     preview without writing
    arachna --clean             remove collected files
    arachna --list              show profiles
    arachna --validate          check config for errors
    arachna --doctor            run full diagnostic
    arachna --install-hook      install git post-commit hook

## Options

| Option | Description |
|--------|-------------|
| --output-dir path | where to write (default: arachna_context/) |
| --verbose | show skipped files |
| --compress | remove blank lines and trailing spaces |
| --incremental | only files changed since last run |
| --format xml,json | markdown (default), xml, or json |
| --merge | append to existing output instead of replacing |
| --dry-run | preview without writing files |
| --force | force overwrite with --install-hook |

## Safety

Commands in .arachna.json (pre_commands, post_commands, command) are validated before execution. Unknown or dangerous commands are blocked by default. Use --dry-run to preview what will be executed before running.

## Doctor

arachna --doctor runs a full diagnostic of your configuration — validates all profiles, checks that directories and files exist, and verifies .gitignore integration. Use it when something doesn't work as expected.

## Git hooks

arachna --install-hook installs a post-commit hook that automatically runs arachna after each commit. Configure the command in .arachna.json:

```json
{
  "hook": {
    "post-commit": "arachna --all --incremental"
  }
}
```

## Configuration (.arachna.json)

arachna uses profiles to define what and how to collect.

Example for a Python project:

```json
{
  "project_name": "MyProject",
  "profiles": {
    "code": {
      "split_mode": "by_file",
      "directories": ["src", "app"],
      "patterns": ["*.py"],
      "files": ["pyproject.toml", "requirements.txt"],
      "pre_commands": ["tree src app"],
      "max_tokens": 16000
    },
    "tests": {
      "split_mode": "by_file",
      "directories": ["tests"],
      "patterns": ["*.py"],
      "max_tokens": 16000
    },
    "docs": {
      "split_mode": "by_file",
      "files": ["README.md", "TODO.md", "CHANGELOG.md"],
      "max_tokens": 16000
    },
    "git": {
      "split_mode": "by_marker",
      "split_marker": "\n=== COMMIT:",
      "command": "git log --reverse --format='=== COMMIT: %h ===%nTITLE: %s%n%nMESSAGE:%n%b%n'",
      "max_tokens": 16000
    }
  }
}
```

## Split modes

- by_file: code and docs, each file stays intact (default)
- by_paragraph: logs, splits on blank lines
- by_marker: git history, splits on custom marker
- single: everything in one file, truncates if too big

## All config fields

- split_mode: by_file, by_paragraph, by_marker, or single
- split_marker: string for by_marker mode
- directories: folders to scan
- patterns: glob patterns like ["*.py"]
- files: specific files to include
- exclude_patterns: glob patterns to skip
- pre_commands: shell commands before collection
- post_commands: shell commands after collection
- command: use command output instead of files
- max_tokens: token limit per output file
- section_format: markdown, xml, or json
- compress: enable safe whitespace compression (blank lines, trailing spaces). Does not modify indentation.
- include_binary: include binaries as base64 (true/false)
- binary_extensions: whitelist like [".png"]
- binary_max_mb: max binary file size in MB

## Output

Files go to arachna_context/ (configurable):

    arachna_context/
      .arachna_manifest.json
      chat-manifest.md          # summary of all files
      chat-code.md
      chat-tests.md
      chat-docs.md
      chat-git.md

When content exceeds max_tokens, files are numbered: chat-code_1.md, chat-code_2.md...

## Manifest and cleanup

Every created file is tracked in .arachna_manifest.json. Running --all again removes old files automatically. With --profile, only that profile's files are cleaned.

## Incremental mode

With --incremental, arachna skips files unchanged since last run. Uses .arachna_cache.json.

## Tokenizer

arachna uses a conservative estimate: 4 characters = 1 token.
This works for any model with a 20-30% safety margin.

### Built-in (default)

No dependencies. Always works. Set max_tokens below your model's context window:
- 8192 window → max_tokens: 6000
- 32768 window → max_tokens: 24000

### Custom tokenizer

Add to your .arachna.json:

      "tokenizer": "my_module:count_tokens"

Your module must export count_tokens(text) -> int. Example:

    # my_tok.py
    def count_tokens(text: str) -> int:
        return max(1, len(text) // 4)  # your logic here

### Cloud models

For exact token counts with cloud APIs, install tiktoken:

    pip install tiktoken

      "tokenizer": "tiktoken:cl100k_base"    # GPT-4, DeepSeek
      "tokenizer": "tiktoken:o200k_base"     # GPT-4o

### Local models

For exact token counts with HuggingFace tokenizers, install transformers:

    pip install transformers

      "tokenizer": "transformers:Qwen/Qwen2.5-7B-Instruct"
      "tokenizer": "transformers:mistralai/Mistral-7B-Instruct-v0.3"
      "tokenizer": "transformers:google/gemma-7b"

Note: transformers is a heavy dependency (gigabytes). Use only if you need exact counts.
For most local models, the built-in estimate with safety margin is sufficient.

## Supported project types

arachna --init auto-detects 17 project types:

### Languages
- Python: src/, app/, lib/, pkg/, scripts/, *.py, pyproject.toml
- JavaScript/TypeScript: src/, app/, lib/, *.js, *.ts, package.json
- C/C++: src/, include/, *.c, *.cpp, *.h, CMakeLists.txt
- C#: *.cs, *.csproj, *.sln
- Swift: Sources/, *.swift, Package.swift
- Kotlin/Java: src/, *.kt, *.java, build.gradle, pom.xml
- Ruby: lib/, app/, *.rb, Gemfile
- PHP: src/, app/, public/, *.php, composer.json

### Engines
- Godot: *.gd, *.tscn, *.tres, project.godot
- Unity: Assets/, *.cs, *.unity, *.prefab
- Unreal Engine: Source/, Content/, *.cpp, *.h, *.cs, *.uproject, *.uplugin

### Infrastructure
- Docker: Dockerfile, docker-compose.yml
- Terraform: *.tf, *.tfvars

### Service (always available)
- tests: tests/, test/
- docs: docs/, README.md, TODO.md, CHANGELOG.md, Makefile
- config: pyproject.toml, package.json, go.mod, Cargo.toml, requirements.txt
- git: git log --reverse with commit history

### Custom presets

Create presets.json in your project root to add or override presets:

```json
{
  "my_game": {
    "dirs": ["game"],
    "patterns": ["*.lua"],
    "max_tokens": 8000,
    "split_mode": "by_file",
    "detect": ["game"]
  }
}
```

Use with: arachna --init --preset my_game

## Links

- [GitHub Repository](https://github.com/dead-duke/arachna)
- [Issue Tracker](https://github.com/dead-duke/arachna/issues)
- [Changelog](https://github.com/dead-duke/arachna/blob/main/CHANGELOG.md)

## License

GNU Affero General Public License v3.0 (AGPL-3.0)
See [LICENSE](LICENSE) for full text.
