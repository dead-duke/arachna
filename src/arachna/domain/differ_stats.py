"""Diff statistics — pure functions on DiffSection.

compute_diff_stats is a pure function that operates on DiffSection
data from domain/api_types.py. It lives in domain/ because it has
no dependencies on snapshot/ internals.
"""

from .api_types import DiffSection
from .tokenization.tokenizer import count_tokens


def compute_diff_stats(diffs: list[DiffSection]) -> dict:
    modified = added = deleted = renamed = moved = tokens = 0
    for d in diffs:
        if d.type == "modified":
            modified += 1
        elif d.type == "added":
            added += 1
        elif d.type == "deleted":
            deleted += 1
        elif d.type == "renamed":
            renamed += 1
        elif d.type == "moved":
            moved += 1
        tokens += count_tokens(d.content)
    return {
        "modified": modified,
        "added": added,
        "deleted": deleted,
        "renamed": renamed,
        "moved": moved,
        "tokens": tokens,
    }
