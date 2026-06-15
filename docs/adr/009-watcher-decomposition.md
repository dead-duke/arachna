# ADR-009: watcher.compute_diff decomposed

**Date:** 2026-06-09
**Status:** Accepted

## Context
compute_diff was 130 lines handling 5 content types.

## Decision
Split into _diff_files_sections, _diff_pre_commands_sections, _diff_command_section.

## Consequences
Adding content type isolated to one function.
