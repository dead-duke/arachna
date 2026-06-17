# Security Architecture

## Trust Model

arachna executes shell commands from `.arachna.json` configuration.
The `.arachna.json` file is a **trust boundary** — commands defined in
`pre_commands` and `post_commands` run with the user's permissions.

**Never add commands to `.arachna.json` that you wouldn't run yourself in a terminal.**

## Attack Surface

### Command Execution (domain/runner.py)

Commands come from two sources: user config (pre_commands, post_commands, command)
and internal calls (store operations, Watch subsystem). Each uses a different
security level.

### Tokenizer Loading (domain/tokenizer.py)

Custom tokenizer spec in profile `tokenizer` field triggers `importlib.import_module()`.
Malicious tokenizer files could execute arbitrary code at import time.

### Snapshot Storage (watch/store.py)

Snapshot IDs from CLI arguments are used as filesystem paths.
Malicious IDs could traverse directories.

### Presets Fetching (config/presets.py)

`arachna presets update` downloads JSON from remote URLs.
Malicious presets could inject unsafe tokenizer specs or invalid configs.

### Remote Repository Collection (domain/remote.py)

`arachna collect --repo` clones git repositories from user-supplied URLs.
Malicious URLs could point to repositories with harmful `.arachna.json`
configs or pre_commands.

## Mitigations

### Two-Level Command Sandbox

| Mode | Allowlist | Shell | Pipes | Used For |
|------|-----------|-------|-------|----------|
| Restricted | echo, pwd, date, whoami, id, uname, which, true, false, test | No | No | Internal calls |
| Pre_commands | cat, ls, tree, grep, git, diff, sort, wc, head, tail, cut, tr, comm, join, paste | Yes | Yes | User config |

**Restricted mode** is the default. Commands are executed without shell,
pipes are blocked, only 11 safe commands allowed. Used for all internal calls.

**Pre_commands mode** is enabled explicitly via `allow_file_args=True`.
Used only for pre_commands, post_commands, and command from `.arachna.json`.
Shell is enabled (required for `2>/dev/null` in legitimate tree/git commands).
Pipes are allowed — each pipe part is validated against the allowlist individually.
Redirection is not blocked — user controls their own config file.

**Blocked patterns** apply to both modes. Defined in `domain/runner.py`:
`_BLOCKED_WORDS` (curl, wget, find, eval, etc.) and `_BLOCKED_PHRASES`
(rm -rf /, dd if=, fork bomb patterns). Matching is word-boundary for
words, substring for phrases.

**Design note:** pre_commands can read arbitrary files (`cat /etc/passwd` works).
This is by design — the user explicitly configures these commands.
The allowlist restricts to read-only utilities. Write operations (rm, mv, cp, chmod,
chown, mkdir, touch, tee, xargs, sed, awk) are not in the allowlist.

### Tokenizer Validation

`_is_safe_tokenizer()` in `domain/tokenizer.py` validates tokenizer specs:

1. `default` — always safe (built-in char-counting)
2. `tiktoken`, `transformers` — in `_SAFE_TOKENIZERS` allowlist
3. Additional safe modules via `ARACHNA_SAFE_TOKENIZERS` env var
4. Local `.py` files — AST validation via `_safe_local_imports()`:
   - Imports checked against `_SUSPICIOUS_MODULES` (os, subprocess, sys, etc.)
   - Top-level statements: only `FunctionDef`, `ClassDef`, `Import`, `ImportFrom`, `Assign` allowed
   - `Call` and `Expr` rejected — prevents code execution at import time

### Snapshot ID Validation

`validate_snapshot_id()` in `watch/store.py` enforces `^[\w][\w.-]*$`:
no path separators, no shell metacharacters. Applied to all store operations.

### URL Validation

All user-supplied URLs (`--repo`, `--url` for presets, `fetch_presets()`,
`collect_remote()`) are validated to only allow `http://` and `https://`
schemes. File, FTP, and other schemes are rejected.

HTTP is allowed intentionally — users may host presets or git repositories
on local network servers without TLS. This is a deliberate trade-off:
convenience for local development over strict transport security. Users
who need HTTPS can use it; arachna does not force either.

For remote collection, the cloned repository's `.arachna.json` is treated
as untrusted — pre_commands from cloned repos are NOT executed. arachna
only collects files and auto-detects presets.

### Output Size Limit

`_MAX_OUTPUT_SIZE` (default 10MB, configurable via `ARACHNA_MAX_OUTPUT_SIZE`)
limits command output. When exceeded, the process is killed and output
truncated with a marker. Prevents memory exhaustion from runaway commands.

### Atomic Writes

All persistent writes (cache, manifest, store objects, snapshots) use
`tempfile.mkstemp()` + `os.replace()`. Power loss or crash during write
cannot corrupt existing data — the write either completes or the old
file remains intact.

### Audit Log

All command executions logged to `.arachna_commands.log`:
- Format: `[ISO timestamp] STATUS: command`
- Newlines sanitized: `\n` → `\\n`, `\r` → `\\r`
- Log path search: up to 5 parent directories for `.arachna.json`

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `ARACHNA_MAX_HASH_SIZE` | 10MB | Max file size for SHA256 cache hashing |
| `ARACHNA_SAFE_TOKENIZERS` | tiktoken,transformers | Additional safe tokenizer modules |
| `ARACHNA_PRE_COMMAND_DELAY` | 0 | Seconds delay between pre_commands |
| `ARACHNA_MAX_OUTPUT_SIZE` | 10MB | Max bytes from a single command |
| `ARACHNA_MAX_WORKERS` | 1 | Parallel file I/O workers (opt-in for HDD/network drives) |
| `ARACHNA_CHARS_PER_TOKEN` | 4 | Token estimation ratio |
| `ARACHNA_PRESETS_TIMEOUT` | 10 | Timeout for presets update HTTP fetch |
