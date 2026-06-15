# ADR-003: Language sets — single source of truth

**Date:** 2026-06-09
**Status:** Accepted

## Context
C_LIKE_LANGS and SCRIPT_LANGS defined in 4 modules, had diverged.

## Decision
Define in formatter.py. All modules import from formatter.

## Consequences
Adding a language requires editing one file.
