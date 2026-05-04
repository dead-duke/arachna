# arachna

Context collector for AI — gathers project files into token-limited chunks.

## Install

`pip install arachna`

## Quick start

Create .arachna.json in your project root:
```json
{
  "project_name": "MyProject",
  "output_dir": ".",
  "profiles": {
    "code": {
      "title_template": "# {project_name} — CODE (part {part})\\n\\n",
      "name_template": "chat-code",
      "split_mode": "by_file",
      "directories": ["src"],
      "patterns": ["*.py"],
      "pre_commands": ["tree -I '__pycache__|*.pyc' src || ls -la src"],
      "max_tokens": 16000
    }
  }
}
```

## Usage

arachna --profile code      # collect one profile
arachna --all               # collect all profiles
arachna --clean             # remove all collected files
arachna --list              # list configured profiles

## Config fields

project_name — Project name for title template
output_dir — Where to write output files
profiles.<name>.title_template — Title with {project_name} and {part}
profiles.<name>.name_template — Output filename base
profiles.<name>.split_mode — by_file, by_paragraph, by_marker, or single
profiles.<name>.split_marker — Marker string for by_marker mode
profiles.<name>.directories — Directories to scan
profiles.<name>.patterns — Glob patterns for files
profiles.<name>.files — Specific files to include
profiles.<name>.exclude_patterns — Glob patterns to exclude
profiles.<name>.pre_commands — Shell commands run before file collection
profiles.<name>.command — If set, runs command instead of file collection
profiles.<name>.max_tokens — Token limit per output file

## Split modes

by_file — Each file is atomic, never split. Default.
by_paragraph — Split by double newlines. Good for logs.
by_marker — Split by split_marker string. Good for git log.
single — No split, truncate if exceeds limit.

## Token counting

Conservative estimate: 4 characters ≈ 1 token.
No external dependencies — works for any local model.

## License

MIT