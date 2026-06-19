# Benchmarks

Run: make benchmark
Date: 2026-06-19
Version: v5.1.1
Machine: macOS 26.x, Apple M-series, Python 3.14.0

Methodology: Time measured with time.perf_counter(), warm-up run before measurement.
Token counts from arachna's default tokenizer (4 chars/token).

## Mode comparison (1000 Python files)

| Mode | Parts | Tokens | Time | Throughput | vs full tokens |
|------|-------|--------|------|------------|-----------------|
| full | 3 | 101343 | 0.113s | 27 files/s | baseline |
| repo-map | 1 | 33374 | 0.178s | 11 files/s | -67% |
| headers | 3 | 89260 | 0.151s | 33 files/s | -12% |
| compress | 3 | 52414 | — | — | -1.9% vs no-compress |
| query (1 match) | 1 | 157 | 0.020s | 1 file | -99.8% |

## Streaming: 5000 files

| Metric | Value |
|--------|-------|
| Parts | 11 |
| Tokens | 513313 |
| Time | 0.726s |
| RSS | 154 MB |

## Streaming: 50000 files (stress test)

| Metric | Value |
|--------|-------|
| Parts | 153 |
| Tokens | 5232508 |
| Time | 23.8s |
| RSS | 221 MB |

## Compress: files with blank lines

| Mode | Tokens | Savings |
|------|--------|---------|
| no compress | 53414 | baseline |
| compress | 52414 | -1.9% |

## Incremental: unchanged files

| Metric | Value |
|--------|-------|
| First run files | >=1 |
| Second run files | 0 |
| Second run time | 0.009s |
| First run time | 0.059s |

## Plugin: tree-sitter JavaScript (1000 files)

| Mode | Parts | Tokens | Time |
|------|-------|--------|------|
| full | 4 | 109659 | 0.118s |
| repo-map | 2 | 62413 | 0.140s |

## Structural diff: Python vs JavaScript (500 files each)

| Language | Parts | Tokens | Time |
|----------|-------|--------|------|
| Python (AST) | 2 | 52081 | 0.060s |
| JavaScript (tree-sitter) | 2 | 55136 | 0.057s |

Tree-sitter structural diff for JavaScript performs on par with Python's
built-in AST structural diff (JS 1.99x slower per iteration, but still
sub-millisecond). Both deliver accurate block-level diffs.

## Large files: 10 x 1MB

| Metric | Value |
|--------|-------|
| Parts | 20 |
| RSS | 227 MB |

## Unicode: 100 Cyrillic + 100 CJK

| Metric | Value |
|--------|-------|
| Tokens | 10367 |
