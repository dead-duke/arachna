# ADR-006: Snapshot ID validation

**Date:** 2026-06-09
**Status:** Accepted

## Context
snapshot_id used directly in Path() — path traversal possible.

## Decision
validate_snapshot_id(sid) enforces ^[\w][\w.-]*$.

## Consequences
No path traversal via snapshot names.
