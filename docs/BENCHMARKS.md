# Benchmarks: arachna v2.9.2

Run: `python -m pytest tests/benchmark/ -v -s`
Date: 2026-06-09
Machine: macOS 15.x, Apple M-series, Python 3.14.0

Methodology: Time measured with `time.perf_counter()`, warm-up run before measurement.
Token counts from arachna's default tokenizer (4 chars/token).

## Mode comparison (1000 files)

Setup: 1000 Python files, function + class with methods (~300 chars each).

| Mode | Parts | Tokens | Time | vs full tokens |
|------|-------|--------|------|-----------------|
| full | 3 | 73591 | 0.047s | baseline |
| repo-map | 1 | 33374 | 0.106s | -55% |
| headers | 3 | 89260 | 0.087s | +21% |
| query (1 match) | 1 | 101 | 0.020s | -99.9% |

Repo-map reduces tokens by 55% compared to full mode — only function/class
signatures, no bodies. Headers add 21% overhead for dependency/export metadata.
Query filtering reduces output to single matched file.

## Streaming: 5000 files

Setup: Same files as above, 5000 count.

| Metric | Value |
|--------|-------|
| Parts | 11 |
| Tokens | 375686 |
| Time | 0.297s |

Streaming keeps memory at O(max_tokens) independent of file count.
5000 files collected without loading all content into memory.
Parts are packed densely within 32768 token limit.

## Compress: files with blank lines

Setup: 1000 files with extra blank lines (3 blank lines between statements).

| Mode | Tokens | Savings |
|------|--------|---------|
| no compress | 23651 | baseline |
| compress | 22651 | -4.2% |

Compress strips trailing whitespace and collapses 3+ blank lines to 2.
For files with significant whitespace overhead, savings are higher.

## Incremental: unchanged files

Setup: 500 files, first run populates cache, second run has no changes.

| Metric | Value |
|--------|-------|
| First run files | ≥1 |
| Second run files | 0 |
| Second run time | 0.007s |
| First run time | 0.034s |

Cache hit via mtime_ns + size fast path — no SHA256 fallback needed
when files are untouched between runs.
