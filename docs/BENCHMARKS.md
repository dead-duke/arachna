# Benchmarks

Run: make benchmark
Date: 2026-06-16
Version: v4.1.0
Machine: macOS 26.x, Apple M-series, Python 3.14.0

Methodology: Time measured with time.perf_counter(), warm-up run before measurement.
Token counts from arachna's default tokenizer (4 chars/token).

## Mode comparison (1000 Python files)

| Mode | Parts | Tokens | Time | Throughput | vs full tokens |
|------|-------|--------|------|------------|-----------------|
| full | 3 | 73591 | 0.050s | 60 files/s | baseline |
| repo-map | 1 | 33374 | 0.104s | 10 files/s | -55% |
| headers | 3 | 89260 | 0.082s | 37 files/s | +21% |
| query (1 match) | 1 | 101 | 0.020s | 1 file | -99.9% |

## Streaming: 5000 files

| Metric | Value |
|--------|-------|
| Parts | 11 |
| Tokens | 375686 |
| Time | 0.402s |
| RSS | 92 MB |

## Streaming: 50000 files (stress test)

| Metric | Value |
|--------|-------|
| RSS | < 250 MB |

## Compress: files with blank lines

| Mode | Tokens | Savings |
|------|--------|---------|
| no compress | 23651 | baseline |
| compress | 22651 | -4.2% |

## Incremental: unchanged files

| Metric | Value |
|--------|-------|
| First run files | >=1 |
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

## Large files: 10 x 1MB

| Metric | Value |
|--------|-------|
| Parts | > 1 |
| RSS | < 200 MB |

## Unicode: 100 Cyrillic + 100 CJK

| Metric | Value |
|--------|-------|
| Tokens | > 0 |
