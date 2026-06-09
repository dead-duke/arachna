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
