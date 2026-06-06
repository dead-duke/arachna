"""Example: Delirium agent using arachna Watch API.

This example shows how an AI agent framework (Delirium) can use
arachna's snapshot and diff API for incremental context management.

Pattern:
1. start_task() — create snapshot, collect repo-map for overview
2. get_context() — diff from snapshot (only changes, 10-50x savings)
3. finish_task() — cleanup

Run:
    python examples/delirium_agent.py
"""

from arachna import watch
from arachna.collect_api import collect


class DeliriumAgent:
    """AI agent that uses arachna for efficient context management."""

    def __init__(self, profile: str = "full"):
        self.profile = profile
        self.snapshot_id = None
        self.task_name = None

    def start_task(self, task_name: str) -> str:
        """Create a baseline snapshot before the agent starts working.

        Returns repo-map (signatures only) for quick project overview.
        """
        self.task_name = task_name
        self.snapshot_id = watch.create_snapshot(
            profile=self.profile,
            name=f"task-{task_name}",
        )
        print(f"[{task_name}] Snapshot '{self.snapshot_id}' created")

        # First run — repo-map for overview (saves 50-70% tokens)
        result = collect(profile=self.profile, mode="repo-map")
        overview = result.parts[0] if result.parts else ""
        print(f"[{task_name}] Overview: {result.tokens} tokens")
        return overview

    def get_context(self, query: str | None = None) -> str:
        """Get current context for the AI.

        If a snapshot exists, returns only changes since the baseline
        (10-50x token savings). If no snapshot, returns full context.
        If query is provided, filters to relevant files.
        """
        if not self.snapshot_id:
            result = collect(profile=self.profile, query=query)
            return result.parts[0] if result.parts else ""

        diff = watch.compute_diff(
            snapshot_id=self.snapshot_id,
            profile=self.profile,
        )

        # If changes are too large, fall back to full context
        if diff.stats.tokens > 10000:
            print(
                f"[{self.task_name}] Changes too large "
                f"({diff.stats.tokens} tokens), using full context"
            )
            result = collect(profile=self.profile, query=query)
            return result.parts[0] if result.parts else ""

        print(
            f"[{self.task_name}] Diff: {diff.stats.modified} modified, "
            f"{diff.stats.added} added, {diff.stats.tokens} tokens"
        )

        # Build diff content for the AI
        parts = []
        for section in diff.sections:
            if section.content.strip():
                parts.append(section.content)
        return "\n".join(parts)

    def finish_task(self) -> None:
        """Clean up after task completion."""
        if self.snapshot_id:
            watch.delete_snapshot(self.snapshot_id)
            print(f"[{self.task_name}] Snapshot '{self.snapshot_id}' deleted")
            self.snapshot_id = None
            self.task_name = None

    def update_baseline(self) -> None:
        """Update the baseline snapshot to current state."""
        if self.snapshot_id:
            watch.update_snapshot(self.snapshot_id)
            print(f"[{self.task_name}] Snapshot '{self.snapshot_id}' updated")


def main():
    """Demo: simulate agent workflow."""
    import os
    import tempfile
    from pathlib import Path

    # Setup: create a temporary project
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        src = Path("src")
        src.mkdir()
        (src / "main.py").write_text("def main():\n    print('hello')\n")
        (src / "utils.py").write_text("def helper():\n    return 42\n")

        # Create minimal config
        import json

        Path(".arachna.json").write_text(
            json.dumps(
                {
                    "project_name": "demo",
                    "output_dir": "out",
                    "profiles": {
                        "code": {
                            "directories": ["src"],
                            "patterns": ["*.py"],
                            "max_tokens": 16000,
                            "split_mode": "by_file",
                            "use_gitignore": False,
                        }
                    },
                }
            )
        )

        # Agent workflow
        agent = DeliriumAgent(profile="code")

        # 1. Start task — create baseline, get overview
        overview = agent.start_task("fix-bug-42")
        print(f"\n=== Overview (repo-map) ===\n{overview[:200]}...\n")

        # 2. Agent makes changes to the project
        (src / "main.py").write_text("def main():\n    print('hello world')\n")
        (src / "new_feature.py").write_text("def new_func():\n    return 'feature'\n")

        # 3. Get context — only changes since baseline
        context = agent.get_context()
        print(f"=== Context (diff) ===\n{context[:300]}...\n")

        # 4. Filter by query
        context = agent.get_context(query="main")
        print(f"=== Context (query: 'main') ===\n{context[:300]}...\n")

        # 5. Finish task
        agent.finish_task()


if __name__ == "__main__":
    main()
