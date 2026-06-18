# arachna for LLM Agents

## Why arachna exists

When you work with a project, you don't send the entire codebase on every
message. You send context, get a response, make changes, and continue.
But most tools only solve the first step: "collect all files and send them."

arachna solves the whole cycle. It understands that:

- Context is different for different roles (programmer needs code, tester needs tests)
- After the first message, you don't need to resend unchanged files
- Renamed files should be shown as renames, not delete+add
- Function signatures are often enough — you don't always need bodies
- Line numbers help AI reference specific code locations

## The cycle

arachna is built around a multi-agent workflow:

Architect -> [Programmer <-> Tester] -> Architect

1. **Architect** plans the work in TODO.md, creates specs for complex tasks
2. **Programmer** writes code, runs `make context` to see the project
3. **Tester** writes tests, checks coverage, reports bugs in BUGS.md
4. **Auditor** reviews everything: code, tests, docs, security
5. **Architect** reads the audit, accepts or rejects, plans next cycle

Each role sees different context via profiles:

    arachna collect --profile code     # source code
    arachna collect --profile tests    # test files
    arachna collect --profile docs     # documentation
    arachna collect --profile git      # commit history

## Plugin system (v3.1.0+)

arachna core is zero-dependency. Language-specific features are opt-in plugins:

    # Install accurate structural diff for JavaScript
    pip install arachna[javascript]

    # Install accurate token counting for OpenAI models
    pip install arachna[tiktoken]

    # Or use the plugin manager
    arachna plugins list
    arachna plugins install javascript --execute

Without plugins, arachna falls back to built-in alternatives (text diff,
chars_per_token estimate). Plugins activate automatically when installed.

## Remote repository collection (v4.1.0+)

Collect context from any public git repository without manual cloning:

    arachna collect --repo https://github.com/user/repo
    arachna collect --repo https://github.com/user/repo --profile python

Profile selection logic (v4.1.1+):

- `--profile python` — strict mode: uses the specified profile from the remote
  repo's .arachna.json, or exits with an error listing available profiles
- Without `--profile` — auto-select mode:
  1. If the repo has profiles with `remote: true` field, picks the only one
  2. Multiple `remote: true` profiles — exits with an error, asks for `--profile`
  3. No `remote: true` profiles — auto-detects via `detect_presets()`
  4. Fallback: `"full"` profile

Add `"remote": true` to your profile to mark it as the default for remote collection.

For programmatic use:

```python
from arachna.config.remote import collect_remote

# Auto-detect profile
result = collect_remote("https://github.com/user/repo", profile="full")
print(result)

# Strict profile (error if not found)
result = collect_remote("https://github.com/user/repo", profile="python")
print(result)
```

Clones with `--depth 1` for speed, pre_commands/post_commands are disabled
for security (allow_pre_commands=False). Requires git on PATH.

## Programmatic API

For LLM agents that want to call arachna directly:

```python
from pathlib import Path
from arachna import snapshot
from arachna.collect_api import collect

root = Path.cwd()

# Create a baseline snapshot
sid = snapshot.create_snapshot(root=root, profile="full", name="before-fix")

# Collect context filtered by query
result = collect(root=root, profile="full", query="authentication", mode="repo-map")
for part in result.parts:
    print(part)  # send to LLM

# After changes, get the diff with line numbers
diff = snapshot.compute_diff(
    root=root,
    snapshot_id="before-fix",
    mode="structural",
    line_numbers=True,  # AI can reference specific lines
)
for section in diff.sections:
    print(section.content)  # send to LLM

# Update snapshot for next iteration
snapshot.update_snapshot("before-fix", root=root)
```

## Performance tips

- **Streaming mode** (full) keeps memory at O(max_tokens). Safe for 50K+ files.
- **chars_per_token** for non-English code: `2.5` in profile for Russian/Cyrillic, `1.5` for CJK.
- **write_to_disk=False** in collect_api for agent workflows — no filesystem I/O.
- **line_numbers: true** in profile — AI can reference specific lines in responses.
- **--line-numbers** flag for diff — AI sees exact line numbers in changed blocks (v4.2.0+).
- **max_tokens: -1** for unlimited output — single file, no splitting.
- **Plugins** for non-Python languages — tree-sitter structural diff for JS/TS/Go.
- **Benchmarks** at [docs/BENCHMARKS.md](https://github.com/dead-duke/arachna/blob/main/docs/BENCHMARKS.md).

## Tips for LLM agents

1. **Start with repo-map.** Before reading any code, get the project structure.
   Repo-map saves 50-70% tokens compared to full source.

2. **Use query to narrow focus.** `--query "auth"` with import chain
   gives you the auth module and everything that imports it.

3. **Diff after every change.** Don't ask "what did I change" —
   arachna tells you. Send the diff to verify correctness.

4. **One snapshot per task.** Create a snapshot before each task.
   When the task is done, delete it. Keeps the store clean.

5. **Profiles for separation.** Don't send tests to the programmer agent.
   Don't send source to the tester agent. Use profiles.

6. **Skip pre_commands for speed.** `--no-pre-commands` skips git log
   and tree output — useful when you only need source files.

7. **Install plugins for non-Python code.** `pip install arachna[javascript]`
   for accurate structural diff — AI sees changed functions, not changed lines.

8. **Use --repo for quick exploration.** `arachna collect --repo <url>` clones
   and collects in one command. Add `"remote": true` to your .arachna.json
   to auto-select the right profile for remote collection.

9. **Enable line numbers for precise feedback.** `--line-numbers` on diff
   lets AI say "line 47 has a bug" instead of "the third line in the second
   REMOVED block". More precise = fewer iterations.
