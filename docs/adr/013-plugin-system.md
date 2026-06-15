# ADR-013: Plugin system — opt-in, zero-dep core preserved

**Date:** 2026-06-09
**Status:** Accepted

## Context
Tree-sitter and tiktoken are heavy deps.

## Decision
Python extras + lazy imports. Core stays zero-dep. Environment detector.

## Consequences
Per-language extras in pyproject.toml. Core importable without any optional deps.
