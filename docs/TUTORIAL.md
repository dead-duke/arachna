# arachna Agent API — Tutorial

## Quick start

```python
from pathlib import Path
from arachna import snapshot
from arachna.collect_api import collect

root = Path.cwd()

# 1. Create a snapshot of your project
snapshot_id = snapshot.create_snapshot(root=root, profile="full", name="baseline")
print(f"Snapshot '{snapshot_id}' created")

# 2. Collect full context for the AI
result = collect(root=root, profile="full")
print(f"Collected {result.tokens} tokens in {len(result.parts)} parts")

# 3. Make changes to your project...

# 4. See what changed
diff = snapshot.compute_diff(root=root, snapshot_id="baseline", profile="full")
print(f"Modified: {diff.stats.modified}, Added: {diff.stats.added}")

# 5. Send diff to the AI (only 1-5K tokens instead of 50K+)
for section in diff.sections:
    if section.path:
        print(section.content)
```

## Diff with line numbers (v4.2.0+)

```python
# Line numbers help AI reference specific lines in responses
diff = snapshot.compute_diff(
    root=root,
    snapshot_id="baseline",
    profile="full",
    line_numbers=True,
)
for section in diff.sections:
    if section.path:
        print(section.content)
# Output:
#   REMOVED lines 45-47:
#      45|     total = 0
#      46|     for item in items:
#      47|         total += item.price
```

Or via CLI:

    arachna diff --from baseline --line-numbers

## Remote repository collection (v4.1.0+)

```python
from arachna.config.remote import collect_remote

# Collect context from any public repo in one line
result = collect_remote("https://github.com/user/repo", profile="full")
print(result)
# Repository: https://github.com/user/repo
# Profile: python
# Files collected: 12
# Parts: 1
# Tokens: 45000

# With strict profile (error if not found in remote config)
result = collect_remote("https://github.com/user/repo", profile="python")

# With custom output directory
result = collect_remote("https://github.com/user/repo", output_dir="my_context")
```

Profile selection (v4.1.1+):
- `profile="python"` — strict mode: exact match or ValueError
- `profile="full"` — auto-select: picks `remote: true` profile, or auto-detects via presets, or falls back to "full"
- Add `"remote": true` to your .arachna.json profile to mark it as the default for remote collection

Or via CLI:

    arachna collect --repo https://github.com/user/repo
    arachna collect --repo https://github.com/user/repo --profile python

Clones with `--depth 1` for speed, pre_commands/post_commands are disabled
for security. Requires git on PATH.

## Installing plugins (v3.1.0+)

```python
# Install accurate structural diff for JavaScript
import subprocess
subprocess.run(["pip", "install", "arachna[javascript]"])

# Or use the plugin manager
from arachna.plugins import install_plugin
result = install_plugin("javascript", execute=True)
print(result)
```

## In-memory collection (v2.9.2+)

```python
# Collect without writing files to disk — for AI agents
result = collect(root=root, profile="full", write_to_disk=False)
print(f"Collected {result.tokens} tokens in {len(result.parts)} parts")

# Stream content directly to the model
for part in result.parts:
    response = model.generate(part)
```

## Token estimation for non-English code (v2.9.2+)

```python
# Adjust chars_per_token for Russian/Cyrillic
result = collect(root=root, profile={"directories": ["src"], "patterns": ["*.py"], "chars_per_token": 2.5})
# Default 4 chars/token underestimates Cyrillic by ~60%
```

## Line numbers (v4.1.0+)

```python
# Enable line numbers in profile for AI to reference specific lines
result = collect(root=root, profile={
    "directories": ["src"],
    "patterns": ["*.py"],
    "line_numbers": True,
})
# Output:
# ### src/main.py
#
# ```python
#     1| import os
#     2|
#     3| def main():
#     4|     print("hello")
# ```
```

## Unlimited tokens (v4.1.0+)

```python
# max_tokens: -1 means no limit — single file, no splitting
result = collect(root=root, profile={
    "directories": ["src"],
    "patterns": ["*.py"],
    "max_tokens": -1,
})
# All content in one file, never split across parts
```

## Pipeline metrics (v3.6.0+)

```python
result = collect(root=root, profile="full")
print(f"Extract: {result.metrics.extract_time_ms:.1f}ms")
print(f"Transform: {result.metrics.transform_time_ms:.1f}ms")
print(f"Load: {result.metrics.load_time_ms:.1f}ms")
print(f"Files read: {result.metrics.files_read}")
print(f"Tokens raw: {result.metrics.tokens_raw}")
print(f"Tokens compressed: {result.metrics.tokens_compressed}")
```

## Integration with AI agents

```python
from pathlib import Path
from arachna import snapshot
from arachna.collect_api import collect

class AIAgent:
    def __init__(self, profile="full", root=None):
        self.profile = profile
        self.root = root or Path.cwd()
        self.snapshot_id = None

    def start_task(self, task_name: str):
        """Create a baseline snapshot before making changes."""
        self.snapshot_id = snapshot.create_snapshot(
            root=self.root,
            profile=self.profile,
            name=f"task-{task_name}"
        )
        return collect(root=self.root, profile=self.profile, mode="repo-map", write_to_disk=False)

    def get_context(self) -> str:
        """Get only what changed since the baseline."""
        if not self.snapshot_id:
            return collect(root=self.root, profile=self.profile, write_to_disk=False).parts[0]

        diff = snapshot.compute_diff(
            root=self.root,
            snapshot_id=self.snapshot_id,
            profile=self.profile,
            line_numbers=True,  # AI can reference specific lines
        )

        if diff.stats.tokens > 10000:
            return collect(root=self.root, profile=self.profile, write_to_disk=False).parts[0]

        return "\n".join(s.content for s in diff.sections)

    def finish_task(self):
        """Clean up after task completion."""
        if self.snapshot_id:
            snapshot.delete_snapshot(self.snapshot_id, root=self.root)
            self.snapshot_id = None
```

## Error handling

```python
from arachna.api_errors import (
    ArachnaError,
    SnapshotExistsError,
    SnapshotNotFoundError,
    ProfileNotFoundError,
)

try:
    sid = snapshot.create_snapshot(root=root, profile="full", name="my-snap")
except SnapshotExistsError:
    snapshot.update_snapshot("my-snap", root=root)
except ProfileNotFoundError:
    print("Profile 'full' not found in .arachna.json")
except ArachnaError as e:
    print(f"Unexpected error: {e}")
```
