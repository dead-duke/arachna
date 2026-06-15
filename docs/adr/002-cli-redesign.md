# ADR-002: CLI redesign — argparse subparsers

**Date:** 2026-06-09
**Status:** Accepted

## Context
Flat --flag CLI with manual sys.argv parsing. 25+ flags, no hierarchy.

## Decision
argparse subparsers. cli_watch.py deleted. No backward compatibility.

## Consequences
All CLI commands changed. 25+ test files updated.
