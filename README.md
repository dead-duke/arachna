# arachna

Context collector for AI — gathers project files into token-limited chunks.

## What is arachna

arachna is a command-line tool that collects your project's source code and documentation into files ready to be sent to an AI. It understands tokens (not lines) and splits output smartly so nothing gets cut in the middle.

## Why arachna

- Token-aware splitting: other tools split by lines, arachna splits by tokens
- Zero dependencies: just Python stdlib
- Multiple profiles: code, docs, tests, git history
- Smart defaults: arachna --init detects your project in seconds

## Install
```
pip install arachna
```

## Quick start
```
cd your-project
arachna --init
arachna --all
```
Creates arachna_context/ folder with .md files ready for AI.

## Commands
```
arachna --init              interactive setup
arachna --init --defaults   auto-detect everything
arachna --all               collect all profiles
arachna --profile code      collect one profile
arachna --all --dry-run     preview without writing
arachna --clean             remove collected files
arachna --list              show profiles
arachna --validate          check config
```
## Options

--output-dir path           where to write (default: arachna_context/)
--verbose                   show skipped files
--compress                  remove blank lines and trailing spaces
--incremental               only files changed since last run
--format xml                markdown (default), xml, or json

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

by_file: code and docs, each file stays intact (default)
by_paragraph: logs, splits on blank lines
by_marker: git history, splits on custom marker
single: everything in one file, truncates if too big

## All config fields

split_mode: by_file, by_paragraph, by_marker, or single
split_marker: string for by_marker mode
directories: folders to scan
patterns: glob patterns like ["*.py"]
files: specific files to include
exclude_patterns: glob patterns to skip
pre_commands: shell commands before collection
post_commands: shell commands after collection
command: use command output instead of files
max_tokens: token limit per output file
section_format: markdown, xml, or json
compress: enable whitespace compression (true/false)
compress_indent: also compress indentation (true/false)
include_binary: include binaries as base64 (true/false)
binary_extensions: whitelist like [".png"]
binary_max_mb: max binary file size in MB

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

## Token counting

arachna uses a conservative estimate: 4 characters = 1 token.

This works well across most models (LLaMA, Mistral, Qwen, GPT-4) and content types,
especially source code. Actual token counts vary by model and language.

Set max_tokens 20-30% below your model's context window.
For a 16384 token window, use max_tokens: 12000.
arachna splits sooner rather than later — files will always fit.

No external dependencies required — works out of the box for any local model.

## Supported project types

arachna --init auto-detects:

Python: src/, app/, tests/, *.py, pyproject.toml, requirements.txt
JS/TS: src/, tests/, *.js, *.ts, package.json
Go: cmd/, pkg/, *.go, go.mod
Rust: src/, tests/, *.rs, Cargo.toml

Also: README.md, TODO.md, CHANGELOG.md, Makefile, config/, docs/, data/prompts/.

## License

MIT