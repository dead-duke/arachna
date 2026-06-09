# arachna

[![PyPI version](https://img.shields.io/pypi/v/arachna)](https://pypi.org/project/arachna/)
[![Free Software](https://img.shields.io/badge/Free%20Software-AGPLv3-brightgreen.svg)](https://www.gnu.org/philosophy/free-sw.html)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/dead-duke/arachna/actions/workflows/test.yml/badge.svg)](https://github.com/dead-duke/arachna/actions/workflows/test.yml)

Context collector for AI — gathers project files into token-limited chunks.

arachna is built with arachna — 1121 tests, 92% coverage, 200+ commits.

## Who this is for

arachna is for developers who work with AI on real projects — not demos,
not tutorials, not single-file scripts.

It's built for a cycle workflow. Here's an example: you give project
context to a programmer AI and a tester AI, snapshot what they saw.
The tester AI pulls the diff — only what the programmer changed. It
writes tests. The programmer AI pulls the tester's diff — only new
tests, no code resend. Each AI sees exactly what the other did, never
the full project twice.

This saves tokens on every exchange. Local models with limited context
windows or slow prefill can handle large projects — instead of processing
50K tokens of context before every response, they process a 500-token
diff. Heavy prefill becomes a one-time cost, not a per-message tax.

Two AIs or twenty — the pattern scales. Every AI gets full context once,
then diffs forever.

## What I believe

I'm a solo developer building tools for myself. arachna is an indie project —
not a startup, not a company, not a product for sale. Free software. AGPLv3.

I believe AI tools should be independent. Not tied to a specific editor,
cloud provider, or way of working. arachna doesn't lock you in. It prepares
your project for AI to understand. The rest is up to you.

- **Any editor.** Vim, VS Code, Cursor, Emacs — arachna doesn't care where you write code
- **Any LLM.** Local models, cloud APIs, web chats — the brain is your choice
- **Plain files.** No databases, no daemons, no hidden state. Everything is transparent —
  you can cat, grep, diff the output
- **No telemetry.** No tracking, no cloud sync, no phoning home. Your code stays on your machine
- **Zero dependencies.** Just Python 3.11+ stdlib. pip install arachna, that's it
- **Free software, not just open source.** AGPLv3 guarantees the four freedoms.
  No proprietary forks. [What's the difference?](https://www.gnu.org/philosophy/free-sw.html)

## Contents

- [What arachna does](#what-arachna-does)
- [Install](#install)
- [Quick start](#quick-start)
- [Examples](#examples)
- [Commands](#commands)
- [Options](#options)
- [Environment variables](#environment-variables)
- [Profiles](#profiles)
- [Split modes](#split-modes)
- [All config fields](#all-config-fields)
- [Output](#output)
- [Manifest and cleanup](#manifest-and-cleanup)
- [Incremental mode](#incremental-mode)
- [Watch — snapshots and diffs](#watch--snapshots-and-diffs)
- [Safety](#safety)
- [Performance](#performance)
- [Known limitations](#known-limitations)
- [Doctor](#doctor)
- [Git hooks (optional)](#git-hooks-optional)
- [Tokenizer](#tokenizer)
- [Supported project types](#supported-project-types)
- [Links](#links)
- [License](#license)

## What arachna does

arachna collects your project files into files ready to be sent to an AI.
It understands tokens (not lines) and splits output smartly so nothing
gets cut in the middle.

## Install

    pip install arachna

## Quick start

    cd your-project
    arachna --init
    arachna --all

Creates arachna_context/ with .md files ready for AI.

## Examples

### Local model (Ollama)

    arachna --profile code
    cat arachna_context/chat-code_1.md | ollama run qwen2.5:32b

### Cloud API (OpenAI)

    arachna --profile code
    # Then paste arachna_context/chat-code_1.md into chat.openai.com
    # Or use the API:
    curl https://api.openai.com/v1/chat/completions \
      -H "Authorization: Bearer $OPENAI_API_KEY" \
      -d '{"messages": [{"role": "user", "content": "'"$(cat arachna_context/chat-code_1.md)"'"}]}'

### Multiple profiles for different tasks

    # Give code to the Programmer agent
    arachna --profile code

    # Give tests to the Tester agent
    arachna --profile tests

    # Give docs to the Auditor agent
    arachna --profile docs

    # Give git history for context
    arachna --profile git

### Skip pre_commands for quick collection

    arachna --profile code --no-pre-commands

### Incremental mode (only changed files)

    arachna --profile code --incremental
    # First run: collects everything
    # Second run: skips unchanged files, creates nothing

### Agent workflow with snapshots

    arachna --snapshot create --profile code --name "baseline"
    # ... AI makes changes to your project ...
    arachna --diff --from baseline
    # Sends only the diff, not the full project

### Full project as diff (no snapshot needed)

    arachna --diff --all --profile code
    arachna --diff --all --profile code --mode repo-map

### Dry-run (preview without writing)

    arachna --all --dry-run

### Safety check

    arachna --validate
    # Checks config for errors, exits 1 if problems found

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
    arachna --install-hook      install post-commit git hook (optional)
    arachna --presets-update    update presets from remote repository

### Watch commands

    arachna --snapshot                          show usage hint
    arachna --snapshot list                     list all snapshots
    arachna --snapshot create --profile X --name Y   create snapshot
    arachna --snapshot update <id>              update snapshot
    arachna --snapshot delete <id>              delete snapshot
    arachna --snapshot info <id>                show snapshot details
    arachna --snapshot rename <old> <new>       rename snapshot
    arachna --diff                              diff from single snapshot (auto)
    arachna --diff --from <id>                  diff from specific snapshot
    arachna --diff --from A --to B              cross-snapshot diff
    arachna --diff --all --profile X            full project as diff (no snapshot)
    arachna --diff --stat                       stats only (no content)
    arachna --diff --flat                       flat output (no grouping)
    arachna --diff --format xml                 XML output
    arachna --diff --mode structural            structural (block-level) diff
    arachna --store stats                       store statistics
    arachna --store gc                          garbage collect

### Collection modes

    arachna --all                               full content (default)
    arachna --all --mode headers                with dependency/export headers
    arachna --all --mode repo-map               signatures only (50-70% less tokens)
    arachna --all --query "authentication"      filter files by query

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
| --query "text" | filter files by query |
| --mode full,headers,repo-map | collection mode |
| --no-pre-commands | skip pre_commands for this run |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| ARACHNA_MAX_HASH_SIZE | 10485760 | Max file size in bytes for SHA256 hashing |
| ARACHNA_SAFE_TOKENIZERS | tiktoken,transformers | Comma-separated safe tokenizer modules |
| ARACHNA_PRE_COMMAND_DELAY | 0 | Seconds to sleep between pre_commands |
| ARACHNA_MAX_OUTPUT_SIZE | 10485760 | Max stdout size in bytes for sandbox commands |
| ARACHNA_CHARS_PER_TOKEN | 4 | Characters per token for default tokenizer |
| ARACHNA_PRESETS_TIMEOUT | 10 | Timeout in seconds for --presets-update |

## Profiles

Profiles let you separate context by role — different context for different AI tasks.

Example .arachna.json for a Python project:

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
- chars_per_token: characters per token for estimation (default: 4)
- section_format: markdown, xml, or json
- compress: safe whitespace compression (blank lines, trailing spaces)
- include_binary: include binaries as base64 (true/false)
- binary_extensions: whitelist like [".png"]
- binary_max_mb: max binary file size in MB
- extends: inherit settings from another profile

## Output

Files go to arachna_context/ (configurable):

    arachna_context/
      .arachna_manifest.json
      chat-manifest.md          # summary of all files
      chat-code_1.md
      chat-tests_1.md
      chat-docs_1.md
      chat-git_1.md
      chat-diff-cycle_1.md      # diff output (includes snapshot name)

When content exceeds max_tokens, files are numbered: chat-code_1.md,
chat-code_2.md...

## Manifest and cleanup

Every created file is tracked in .arachna_manifest.json. Running --all
again removes old files automatically. With --profile, only that
profile's files are cleaned.

## Incremental mode

With --incremental, arachna skips files unchanged since last run.
Uses .arachna_cache.json with mtime_ns + size + SHA256 hashes
(smart hybrid — fast path without hashing, SHA256 fallback for
false positives like git checkout).

## Watch — snapshots and diffs

Watch is a subsystem for incremental AI workflows. Instead of sending
full project context (50k+ tokens) every time, create a snapshot once,
then send only changes (diff) in subsequent iterations.

### How it works

    # Create a baseline snapshot
    arachna --snapshot create --profile code --name "before-refactor"

    # AI or developer makes changes to the project
    # ...

    # See what changed (grouped by type)
    arachna --diff --from before-refactor
    # Output:
    #   ## Changes from before-refactor to current (1 renamed, 2 modified)
    #   ### Renamed
    #   RENAMED: src/old.py → src/new.py
    #   ### Modified
    #   ### src/main.py
    #   REMOVED/ADDED...

    # Cross-snapshot diff (between two snapshots)
    arachna --diff --from v1 --to v2

    # Full project as diff (no snapshot needed)
    arachna --diff --all --profile code
    arachna --diff --all --profile code --mode repo-map

    # Just the stats
    arachna --diff --from before-refactor --stat
    # Modified: 3, Added: 1, Renamed: 1, Deleted: 0

    # Flat output (old format, backward compatible)
    arachna --diff --from before-refactor --flat

    # Structural diff (understands code blocks)
    arachna --diff --from before-refactor --mode structural

### Rename and move detection

arachna automatically detects renamed and moved files:

    # Exact rename (same content hash)
    RENAMED: src/old.py → src/new.py

    # Exact move (same content, different directory)
    MOVED: src/utils.py → lib/utils.py

    # Similar rename (content > 70% similar)
    RENAMED: src/old.py → src/new.py (87% similar)

No git needed — works on any project.

### Headers, query, and repo-map

arachna can add context headers showing dependencies and exports for each file.
Use `--mode headers` or `--query` to auto-enable headers.

    # Collect with dependency/export headers
    arachna --all --mode headers

    # Filter by query (keyword scoring + import chain)
    arachna --all --query "authentication"

    # Repo-map mode — signatures only, no bodies
    arachna --all --mode repo-map
    # 50-70% token savings for project overview

### Content-addressable store

Snapshots are stored in .arachna/store/ (never committed — auto-gitignored).
Files are deduplicated by SHA256 hash. Multiple snapshots share identical
content — only one copy stored.

    arachna --store stats
    # Store statistics:
    #   Snapshots: 5
    #   Objects: 127
    #   Total size: 2.3 MB
    #   Unique content: 1.1 MB (52% deduplication)

    arachna --store gc
    # Removed 15 objects (freed 2.3 MB)

### Snapshot management

    # List all snapshots
    arachna --snapshot list

    # Show snapshot details
    arachna --snapshot info before-refactor

    # Show profile only
    arachna --snapshot info before-refactor --profile

    # Update a snapshot (re-scan current state)
    arachna --snapshot update before-refactor

    # Rename a snapshot
    arachna --snapshot rename before-refactor after-refactor

    # Delete a snapshot (objects survive for other snapshots)
    arachna --snapshot delete before-refactor

### Programmatic API (v2.0.0+)

All Watch and collection features are available as a Python API:

```python
from arachna import watch
from arachna.collect_api import collect

# Create snapshot
sid = watch.create_snapshot(profile="full", name="baseline")

# Collect context
result = collect(profile="full", mode="repo-map")

# Compute diff
diff = watch.compute_diff(snapshot_id="baseline", mode="structural")
print(f"Modified: {diff.stats.modified}, Added: {diff.stats.added}")
```

See [TUTORIAL.md](docs/TUTORIAL.md) for full API documentation
and [LLM_INTEGRATION.md](docs/LLM_INTEGRATION.md) for LLM agent workflow.

### Diff format

Human-readable diff optimized for AI consumption:

    ### src/main.py

    REMOVED lines 45-47:
        total = 0
        for item in items:
            total += item.price

    ADDED lines 45:
        return sum(item.price for item in items)

## Safety

Commands in .arachna.json (pre_commands, post_commands, command) are validated
before execution. arachna uses two security levels:

**Restricted mode** — for internal operations (snapshot names, preset URLs).
Only 11 safe commands allowed: echo, pwd, date, whoami, id, uname, which,
true, false, test, [. No shell metacharacters, no shell=True. This protects
against injection via external input.

**Pre_commands mode** — for your .arachna.json. Extended read-only allowlist:
cat, tree, git, grep, sort, wc, head, tail, diff, and more. Shell=True with
pipes (|, ||, &&) and redirection (>, <) allowed. You control your config —
you are responsible for what's in it.

Snapshot IDs are validated against path traversal (no ../). Tokenizer files
are checked for malicious code before import. Preset URLs are restricted to
http:// and https:// only. Sandbox limits command output to 10MB by default
(ARACHNA_MAX_OUTPUT_SIZE).

Use --dry-run to preview what will be executed.

## Performance

Quick benchmarks on 1000 Python files (Apple M-series, macOS, Python 3.14):

| Mode | Tokens | Time | vs full |
|------|--------|------|---------|
| full (streaming) | 73.6K | 0.05s | baseline |
| repo-map | 33.4K | 0.10s | -55% tokens |
| headers | 89.3K | 0.09s | +21% tokens |
| compress | 22.7K | 0.05s | -4.2% vs no-compress |
| query (1 match) | 101 | 0.02s | -99.9% |
| incremental (unchanged) | 0 | 0.007s | instant |

Full details: [docs/BENCHMARKS.md](docs/BENCHMARKS.md). Run locally: `make benchmark`.

## Known limitations

- **Structural diff for non-Python languages** requires plugins. JavaScript, TypeScript,
  Go, Rust, and C/C++ use text diff by default. Install plugins for accurate
  block-level diffs: `pip install arachna[javascript]` (available in v3.1+)
- **Incremental mode** works best on local machines. In CI/CD with fresh clones,
  all files get new timestamps — cache misses and falls back to full SHA256 hashing.
  Use without `--incremental` in CI.
- **Config inheritance** uses different merge rules for different fields:
  scalars override, exclude lists append, source lists replace. Warnings
  are printed when child overrides parent fields.
- **Repo-map and headers modes** load all file content into memory for parsing
  (AST/regex). For projects with >10K files, use full mode with streaming instead.
- **Streaming mode** (full mode) keeps memory at O(max_tokens). Pre_commands run
  before file collection. Query filtering works on filenames in streaming mode.
- **Snapshot portability** across Windows and Linux — paths stored relative to project root.

## Doctor

arachna --doctor runs a full diagnostic — validates all profiles, checks
that directories and files exist, verifies .gitignore integration.

## Git hooks (optional)

If you prefer git-based workflow, arachna can integrate via post-commit hooks.
But it works fine without git.

    arachna --install-hook

Configure the command in .arachna.json:

```json
{
  "hook": {
    "post-commit": "arachna --all --incremental"
  }
}
```

## Tokenizer

arachna uses a conservative estimate: 4 characters = 1 token.
Works for any model with a 20-30% safety margin.

### Built-in (default)

No dependencies. Always works. Set max_tokens below your model's
context window:
- 8192 window → max_tokens: 6000
- 32768 window → max_tokens: 24000

Adjust `chars_per_token` in your profile for non-English code:
- English: 4.0 (default)
- Russian/Cyrillic: 2.5
- Chinese/Japanese/Korean: 1.5

Or set `ARACHNA_CHARS_PER_TOKEN` environment variable.

### Custom tokenizer

Add to your .arachna.json:

      "tokenizer": "my_module:count_tokens"

Your module must export count_tokens(text) -> int:

    # my_tok.py
    def count_tokens(text: str) -> int:
        return max(1, len(text) // 4)  # your logic here

### Cloud models

For exact token counts, install tiktoken:

    pip install tiktoken

      "tokenizer": "tiktoken:cl100k_base"    # GPT-4, DeepSeek
      "tokenizer": "tiktoken:o200k_base"     # GPT-4o

### Local models

For HuggingFace tokenizers, install transformers:

    pip install transformers

      "tokenizer": "transformers:Qwen/Qwen2.5-7B-Instruct"
      "tokenizer": "transformers:mistralai/Mistral-7B-Instruct-v0.3"
      "tokenizer": "transformers:google/gemma-7b"

Note: transformers is a heavy dependency. For most local models,
the built-in estimate with safety margin is sufficient.

## Supported project types

arachna --init auto-detects 24 project types:

### Languages
- Python: src/, app/, lib/, pkg/, scripts/, *.py, pyproject.toml
- JavaScript/TypeScript: src/, app/, lib/, *.js, *.ts, *.jsx, *.tsx, package.json
- C/C++: src/, include/, *.c, *.cpp, *.h, *.hpp, CMakeLists.txt
- C#: *.cs, *.csproj, *.sln
- Swift: Sources/, *.swift, Package.swift
- Kotlin/Java: src/, *.kt, *.java, build.gradle, build.gradle.kts, pom.xml
- Ruby: lib/, app/, *.rb, Gemfile
- PHP: src/, app/, public/, *.php, composer.json
- Go: *.go, go.mod, go.sum, main.go
- Rust: src/, *.rs, Cargo.toml, Cargo.lock
- Zig: src/, *.zig, build.zig, build.zig.zon
- Lua: src/, lib/, *.lua, *.rockspec
- Elixir: lib/, *.ex, *.exs, mix.exs
- Haskell: src/, app/, *.hs, *.lhs, *.cabal, stack.yaml
- Gleam: src/, *.gleam, gleam.toml, manifest.toml

### Engines
- Godot: *.gd, *.tscn, *.tres, project.godot
- Unity: Assets/, *.cs, *.unity, *.prefab
- Unreal Engine: Source/, Content/, *.cpp, *.h, *.cs, *.uproject, *.uplugin

### Infrastructure
- Docker: Dockerfile, docker-compose.yml
- Terraform: *.tf, *.tfvars

### Service
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

### Presets update

Fetch updated presets from the remote repository:

    arachna --presets-update
    # Merges with built-in presets, local presets.json never overwritten

    arachna --presets-update --url https://example.com/presets.json
    # Use custom URL

## Links

- [GitHub Repository](https://github.com/dead-duke/arachna)
- [Issue Tracker](https://github.com/dead-duke/arachna/issues)
- [Changelog](https://github.com/dead-duke/arachna/blob/main/CHANGELOG.md)
- [Architecture](https://github.com/dead-duke/arachna/blob/main/docs/ARCHITECTURE.md)
- [LLM Integration](https://github.com/dead-duke/arachna/blob/main/docs/LLM_INTEGRATION.md)
- [Benchmarks](https://github.com/dead-duke/arachna/blob/main/docs/BENCHMARKS.md)

## License

arachna is free software licensed under GNU AGPLv3. This license guarantees
the four essential freedoms: to run the program for any purpose, to study
and modify it, to redistribute copies, and to distribute modified versions.

Why AGPLv3 and not MIT or Apache? Because permissive licenses allow
proprietary forks. AGPLv3 ensures that derivative works — including
software running as a network service — remain free. No proprietary
forks. No closed modifications. What the community builds, the community
keeps.

See [LICENSE](LICENSE) for the full legal text.
