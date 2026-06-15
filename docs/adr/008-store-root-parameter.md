# ADR-008: _store_root explicit root parameter

**Date:** 2026-06-09
**Status:** Accepted

## Context
Store tied to Path.cwd() — no isolated stores in one process.

## Decision
_store_root(root: Path | None = None). Tests pass explicit tmp_path.

## Consequences
Backward compatible. No monkeypatch.chdir in store tests.
