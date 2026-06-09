# Benchmarks: arachna v3.1.0

Run: `make benchmark`
Date: 2026-06-09
Machine: macOS 15.x, Apple M-series, Python 3.14.0

Methodology: Time measured with `time.perf_counter()`, warm-up run before measurement.
Token counts from arachna's default tokenizer (4 chars/token).

## Mode comparison (1000 Python files)

| Mode | Parts | Tokens | Time | vs full tokens |
|------|-------|--------|------|-----------------|
| full | 3 | 73591 | 0.055s | baseline |
| repo-map | 1 | 33374 | 0.107s | -55% |
| headers | 3 | 89260 | 0.083s | +21% |
| query (1 match) | 1 | 101 | 0.020s | -99.9% |

## Streaming: 5000 files

| Metric | Value |
|--------|-------|
| Parts | 11 |
| Tokens | 375686 |
| Time | 0.277s |

## Compress: files with blank lines

| Mode | Tokens | Savings |
|------|--------|---------|
| no compress | 23651 | baseline |
| compress | 22651 | -4.2% |

## Incremental: unchanged files

| Metric | Value |
|--------|-------|
| First run files | ≥1 |
| Second run files | 0 |
| Second run time | 0.007s |
| First run time | 0.029s |

## Plugin: tree-sitter JavaScript (1000 files)

| Mode | Parts | Tokens | Time |
|------|-------|--------|------|
| full | 3 | 79647 | 0.050s |
| headers | 3 | 94816 | 0.061s |

## Structural diff: Python vs JavaScript (500 files each)

| Language | Parts | Tokens | Time |
|----------|-------|--------|------|
| Python (AST) | 2 | 37080 | 0.027s |
| JavaScript (tree-sitter) | 2 | 40136 | 0.025s |

Tree-sitter structural diff for JavaScript performs on par with Python's
built-in AST structural diff. Both deliver accurate block-level diffs.
