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

## The cycle

arachna is built around a multi-agent workflow:

```
Техдир -> [Программист <-> Тестировщик] -> Техдир
```

1. **Техдир** plans the work in TODO.md, creates specs for complex tasks
2. **Программист** writes code, runs `make context` to see the project
3. **Тестировщик** writes tests, checks coverage, reports bugs in BUGS.md
4. **Аудитор** reviews everything: code, tests, docs, security
5. **Техдир** reads the audit, accepts or rejects, plans next cycle

Each role sees different context via profiles:

```bash
arachna --profile code     # source code
arachna --profile tests    # test files
arachna --profile docs     # documentation
arachna --profile git      # commit history
```

## Why snapshots and diffs

The key insight: after the first message, most files don't change.
Sending the full project again wastes tokens and dilutes attention.

Instead:

1. Create a snapshot once
2. Work on the project — make changes, run tests, fix bugs
3. See what changed
4. Send only the diff to the LLM — 10-50x fewer tokens

```bash
arachna --snapshot create --profile full --name baseline
# ... work on the project ...
arachna --diff --from baseline
```

The diff is not a raw unified diff. It's structured for AI consumption:

- Rename detection: `RENAMED: src/old.py -> src/new.py` (not delete+add)
- Move detection: `MOVED: src/utils.py -> lib/utils.py`
- Structural diff: shows changed functions, not changed lines
- Grouped output: renamed, moved, modified, added, deleted — each in its own section
- Multi-part summaries: each part shows change counts in the header

## Collection modes

Not every message needs full file contents:

- `--mode full` (default): complete source code
- `--mode headers`: imports and exports — what depends on what
- `--mode repo-map`: function/class signatures — project structure overview
- `--query "authentication"`: filter files by keyword with import chain

A typical session:

```bash
# First message: give the LLM a map of the project
arachna --all --mode repo-map

# Second message: focus on relevant files
arachna --all --mode full --query "auth"

# After changes: show what changed
arachna --diff --from baseline --mode structural
```

## Practical workflow example

A bug is reported: "login fails with Unicode names."

### Step 1: Understand the problem

```bash
arachna --all --query "login auth unicode" --mode repo-map
```

Send to LLM: "Here's the project structure around authentication.
Where should I look for Unicode handling in login?"

### Step 2: Deep dive

```bash
arachna --all --query "login auth" --mode full
```

Send to LLM: "Here are the relevant files. Find the Unicode bug."

### Step 3: Apply the fix

LLM suggests changes. You apply them.

### Step 4: Verify

```bash
arachna --diff --from baseline
```

Send to LLM: "Here's what I changed. Is this correct?
Are there edge cases I missed?"

### Step 5: Update baseline

```bash
arachna --snapshot update baseline
```

### Step 6: Tests

```bash
arachna --profile tests
```

Send to LLM: "Write tests for the Unicode login fix."

This cycle repeats. Each step sends minimal context.
The LLM never sees the whole project at once — only what's relevant.

## Programmatic API

For LLM agents that want to call arachna directly:

```python
from arachna import watch
from arachna.collect_api import collect

# Create a baseline snapshot
sid = watch.create_snapshot(profile="full", name="before-fix")

# Collect context filtered by query
result = collect(profile="full", query="authentication", mode="repo-map")
for part in result.parts:
    print(part)  # send to LLM

# After changes, get the diff
diff = watch.compute_diff(snapshot_id="before-fix", mode="structural")
for section in diff.sections:
    print(section.content)  # send to LLM

# Update snapshot for next iteration
watch.update_snapshot("before-fix")
```

## Snapshot management

Snapshots are stored in `.arachna/store/` (auto-gitignored).
They are content-addressed with SHA256 deduplication.
Multiple snapshots share identical files — only one copy stored.

```bash
arachna --snapshot list              # list all snapshots
arachna --snapshot info baseline     # show details
arachna --snapshot rename old new    # rename
arachna --snapshot delete old        # clean up
arachna --store stats                # disk usage
arachna --store gc                   # remove unreferenced objects
```

## Security model

arachna uses two command execution modes:

- **Restricted mode** for internal operations — 11 safe commands, no shell.
  Protects snapshot names, preset URLs, and other external input from injection.

- **Pre_commands mode** for your `.arachna.json` — git, tree, grep, pipes,
  redirection. Full shell available. You write the config, you own the security.

Pre_commands run with `shell=True`. `2>/dev/null`, `&&`, `||` all work.
This is by design — a config file you control doesn't need protection from
yourself. Snapshot IDs, tokenizer files, and preset URLs are validated
independently against path traversal and code injection.

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

7. **Read the audit.** AUDIT_REPORT.md has security and architecture findings.
   Fix them before writing new code.
