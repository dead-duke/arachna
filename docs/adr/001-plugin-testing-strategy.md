# ADR-001: Plugin testing strategy — real packages locally, mocks in CI

**Date:** 2026-06-09
**Status:** Accepted

## Context
v3.1.0 added optional plugins. Plugin code paths were unreachable in CI.

## Decision
Split testing: requirements-dev.txt for local, CI without plugins. Fallback tests verify error messages.

## Consequences
CI coverage ~91%, local 94%+. No mocking — real integration tested.
