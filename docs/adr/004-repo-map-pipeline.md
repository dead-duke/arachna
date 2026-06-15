# ADR-004: Repo-map pipeline unified

**Date:** 2026-06-09
**Status:** Accepted

## Context
Three parallel repo-map implementations in gatherer, differ_structural, watch.

## Decision
_apply_repo_map_to_sections in gatherer.py is single pipeline.

## Consequences
Changing format requires editing one function.
