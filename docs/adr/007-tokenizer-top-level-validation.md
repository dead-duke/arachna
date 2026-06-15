# ADR-007: Tokenizer top-level statement validation

**Date:** 2026-06-09
**Status:** Accepted

## Context
_safe_local_imports checked imports, not top-level statements.

## Decision
_validate_top_level_statements rejects Call, Expr, Assign-with-calls.

## Consequences
Malicious tokenizer files cannot execute code at import time.
