# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""File exclusion matching — fnmatch patterns with directory support."""

import fnmatch


def _match_directory_pattern(path_str, pat):
    parts = path_str.split("/")
    pat_parts = pat.split("/")
    if len(pat_parts) > len(parts):
        return False
    for start in range(len(parts) - len(pat_parts) + 1):
        suffix = "/".join(parts[start:])
        if fnmatch.fnmatch(suffix, pat):
            return True
    return False


def is_excluded(path, exclude_patterns):
    path_str = str(path).replace("\\", "/")
    for pat in exclude_patterns:
        if "/" in pat:
            if _match_directory_pattern(path_str, pat):
                return True
        elif fnmatch.fnmatch(path_str, pat) or fnmatch.fnmatch(path.name, pat):
            return True
    return False
