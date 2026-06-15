# ADR-012: Zero-dep fixes in pure Python

**Date:** 2026-06-09
**Status:** Accepted

## Context
Audit found 13 issues. 6 need external deps, 7 solvable in stdlib.

## Decision
Solved in stdlib: streaming, TOC indices, config inheritance, snapshot paths, sandbox, chars_per_token.

## Consequences
Memory O(files*100B). External deps deferred to plugins.
