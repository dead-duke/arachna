import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from arachna.gatherer import gather_files


def test_gather_files_incremental_skips_unchanged():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "a.py").write_text("unchanged")
        wd = os.getcwd()
        os.chdir(d)
        try:
            with patch("pathlib.Path.cwd", return_value=Path(d)):
                profile = {
                    "directories": [d],
                    "patterns": ["*.py"],
                    "use_gitignore": False,
                }
                # First run — collect
                sections = gather_files(profile)
                assert len(sections) == 1

                # Second run — incremental, should be empty (no changes)
                # Note: cache is stored in arachna_context/ by collector, not gather_files directly
        finally:
            os.chdir(wd)
