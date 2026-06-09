"""Fixtures and baseline management for benchmarks."""

import json
import os
from pathlib import Path

BASELINE_FILE = Path(__file__).parent / "baseline.json"


def pytest_sessionfinish(session, exitstatus):
    if os.environ.get("UPDATE_BASELINE") and exitstatus == 0:
        from .test_performance import RESULTS

        if RESULTS:
            baseline = {}
            for r in RESULTS:
                name = r["test"]
                baseline[name] = {k: v for k, v in r.items() if k != "test"}
            BASELINE_FILE.write_text(json.dumps(baseline, indent=2))
            print(f"\nBaseline updated: {BASELINE_FILE}")
