# arachna Agent API — Tutorial

## Quick start

```python
from arachna import watch
from arachna.collect_api import collect

# 1. Create a snapshot of your project
snapshot_id = watch.create_snapshot(profile="full", name="baseline")
print(f"Snapshot '{snapshot_id}' created")

# 2. Collect full context for the AI
result = collect(profile="full")
print(f"Collected {result.tokens} tokens in {len(result.parts)} parts")

# 3. Make changes to your project...

# 4. See what changed
diff = watch.compute_diff(snapshot_id="baseline", profile="full")
print(f"Modified: {diff.stats.modified}, Added: {diff.stats.added}")

# 5. Send diff to the AI (only 1-5K tokens instead of 50K+)
for section in diff.sections:
    if section.path:
        print(section.content)
```

## Filtering by query

```python
# Only collect files related to authentication
result = collect(profile="full", query="auth token")

# Query scoring:
# +10: word in filename (auth.py)
# +8: word in function/class names
# +5: word in imports (dependencies)
# +3: word in file content
# Files importing matched files also included (import chain)
```

## Repo-map mode (signatures only)

```python
# Project overview — only function/class signatures
result = collect(profile="full", mode="repo-map")
# Saves 50-70% tokens compared to full mode
```

## Structural diff

```python
# Block-level diff — understands code structure
diff = watch.compute_diff(snapshot_id="baseline", mode="structural")
# Shows MODIFIED/DELETED/ADDED functions and classes
# Not just line ranges
```

## Cross-snapshot diff

```python
# Diff between two historical snapshots
diff = watch.compute_diff(
    snapshot_id="v1",
    to_snapshot_id="v2",
    profile="full"
)
```

## Snapshot management

```python
# List all snapshots
snaps = watch.list_snapshots()
for s in snaps:
    print(f"{s.id}: {s.file_count} files")

# Get snapshot details
info = watch.snapshot_info("baseline")
print(f"Profile dirs: {info.profile.get('directories', [])}")

# Update snapshot (re-scan current state)
watch.update_snapshot("baseline")

# Delete snapshot
watch.delete_snapshot("old-snapshot")
```

## Store management

```python
# Check disk usage
stats = watch.store_stats()
print(f"{stats.snapshots} snapshots, {stats.dedup_pct}% dedup")

# Free space
result = watch.store_gc()
print(f"Freed {result.freed_bytes} bytes")
```

## In-memory collection (v2.9.2+)

```python
# Collect without writing files to disk — for AI agents
result = collect(profile="full", write_to_disk=False)
print(f"Collected {result.tokens} tokens in {len(result.parts)} parts")

# Stream content directly to the model
for part in result.parts:
    response = model.generate(part)
```

## Token estimation for non-English code (v2.9.2+)

```python
# Adjust chars_per_token for Russian/Cyrillic
result = collect(profile={"directories": ["src"], "patterns": ["*.py"], "chars_per_token": 2.5})
# Default 4 chars/token underestimates Cyrillic by ~60%
```

## Integration with AI agents

```python
import arachna.watch as watch
from arachna.collect_api import collect

class AIAgent:
    def __init__(self, profile="full"):
        self.profile = profile
        self.snapshot_id = None

    def start_task(self, task_name: str):
        """Create a baseline snapshot before making changes."""
        self.snapshot_id = watch.create_snapshot(
            profile=self.profile,
            name=f"task-{task_name}"
        )
        # First run — repo-map for project overview
        return collect(profile=self.profile, mode="repo-map", write_to_disk=False)

    def get_context(self) -> str:
        """Get only what changed since the baseline."""
        if not self.snapshot_id:
            return collect(profile=self.profile, write_to_disk=False).parts[0]

        diff = watch.compute_diff(
            snapshot_id=self.snapshot_id,
            profile=self.profile,
        )

        # If changes are too large, treat as full context
        if diff.stats.tokens > 10000:
            return collect(profile=self.profile, write_to_disk=False).parts[0]

        # Otherwise send only the diff
        return "\n".join(s.content for s in diff.sections)

    def finish_task(self):
        """Clean up after task completion."""
        if self.snapshot_id:
            watch.delete_snapshot(self.snapshot_id)
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
    sid = watch.create_snapshot(profile="full", name="my-snap")
except SnapshotExistsError:
    watch.update_snapshot("my-snap")
except ProfileNotFoundError:
    print("Profile 'full' not found in .arachna.json")
except ArachnaError as e:
    print(f"Unexpected error: {e}")
```
