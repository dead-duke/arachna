# ADR-005: Two-level command allowlist

**Date:** 2026-06-09
**Status:** Accepted

## Context
_ALLOWED_COMMANDS allowed arbitrary file reads. But pre_commands need git, tree, pipes.

## Decision
allow_file_args=False: 11 safe commands. allow_file_args=True: extended read-only.

## Consequences
Internal code paths safe. Pre_commands work as before.
