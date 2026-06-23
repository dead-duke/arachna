"""Example: Delirium agent using arachna Snapshot API.

This example shows how an AI agent framework (Delirium) can use
arachna's snapshot and diff API for incremental context management.

Pattern:
1. start_task() — create snapshot, collect repo-map for overview
2. get_context() — diff from snapshot (only changes, 10-50x savings)
3. finish_task() — cleanup

Run:
    python examples/delirium_agent.py
"""

from pathlib import Path

from arachna import snapshot
from arachna.api.collect_api import collect
from arachna.config.core.config import get_profile, load_config
from arachna.config.profile_config import ProfileConfig


class DeliriumAgent:
    """AI agent that uses arachna for efficient context management."""

    def __init__(self, profile: str = "full", root: Path | None = None):
        if root is None:
            raise ValueError("root is required. Pass Path.cwd() explicitly.")
        self.profile = profile
        self.root = root
        self.config = load_config(root=self.root)
        self.snapshot_id = None
        self.task_name = None

    def _resolve_profile(self) -> ProfileConfig:
        return get_profile(self.profile, root=self.root, config=self.config)

    def start_task(self, task_name: str) -> str:
        """Create a baseline snapshot before the agent starts working.

        Returns repo-map (signatures only) for quick project overview.
        """
        self.task_name = task_name
        profile_dict = self._resolve_profile()
        self.snapshot_id = snapshot.create_snapshot(
            root=self.root,
            profile=profile_dict,
            name=f"task-{task_name}",
        )
        print(f"[{task_name}] Snapshot '{self.snapshot_id}' created")

        result = collect(root=self.root, profile=profile_dict, config=self.config, mode="repo-map")
        overview = result.parts[0] if result.parts else ""
        print(f"[{task_name}] Overview: {result.tokens} tokens")
        return overview

    def get_context(self, query: str | None = None) -> str:
        """Get current context for the AI.

        If a snapshot exists, returns only changes since the baseline.
        If query is provided, filters to relevant files.
        """
        profile_dict = self._resolve_profile()
        if not self.snapshot_id:
            result = collect(root=self.root, profile=profile_dict, config=self.config, query=query)
            return result.parts[0] if result.parts else ""

        diff = snapshot.compute_diff(
            root=self.root,
            snapshot_id=self.snapshot_id,
            profile=profile_dict,
        )

        if diff.stats.tokens > 10000:
            print(
                f"[{self.task_name}] Changes too large "
                f"({diff.stats.tokens} tokens), using full context"
            )
            result = collect(root=self.root, profile=profile_dict, config=self.config, query=query)
            return result.parts[0] if result.parts else ""

        print(
            f"[{self.task_name}] Diff: {diff.stats.modified} modified, "
            f"{diff.stats.added} added, {diff.stats.tokens} tokens"
        )

        parts = []
        for section in diff.sections:
            if section.content.strip():
                parts.append(section.content)
        return "\n".join(parts)

    def finish_task(self) -> None:
        """Clean up after task completion."""
        if self.snapshot_id:
            snapshot.delete_snapshot(self.snapshot_id, root=self.root)
            print(f"[{self.task_name}] Snapshot '{self.snapshot_id}' deleted")
            self.snapshot_id = None
            self.task_name = None

    def update_baseline(self) -> None:
        """Update the baseline snapshot to current state."""
        if self.snapshot_id:
            profile_dict = self._resolve_profile()
            snapshot.update_snapshot(
                self.snapshot_id, root=self.root, profile=profile_dict
            )
            print(f"[{self.task_name}] Snapshot '{self.snapshot_id}' updated")


def main():
    """Demo: simulate agent workflow."""
    import json
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        src = root / "src"
        src.mkdir()
        (src / "main.py").write_text("def main():\n    print('hello')\n")
        (src / "utils.py").write_text("def helper():\n    return 42\n")

        (root / ".arachna.json").write_text(
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

        agent = DeliriumAgent(profile="code", root=root)

        overview = agent.start_task("fix-bug-42")
        print(f"\n=== Overview (repo-map) ===\n{overview[:200]}...\n")

        (src / "main.py").write_text("def main():\n    print('hello world')\n")
        (src / "new_feature.py").write_text("def new_func():\n    return 'feature'\n")

        context = agent.get_context()
        print(f"=== Context (diff) ===\n{context[:300]}...\n")

        context = agent.get_context(query="main")
        print(f"=== Context (query: 'main') ===\n{context[:300]}...\n")

        agent.finish_task()


if __name__ == "__main__":
    main()
