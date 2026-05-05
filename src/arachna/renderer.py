"""Renders dry-run output with aligned formatting."""


def _format_pct(tokens: int, max_tokens: int) -> str:
    """Format percentage string."""
    if max_tokens <= 0:
        return "0.0%"
    pct = (tokens / max_tokens) * 100
    if pct < 0.05:
        return "<0.1%"
    return f"{pct:.1f}%"


def _format_line(tokens: int, max_tokens: int, name: str) -> str:
    """Format one line: '  5431 tokens | 34.0% | name'"""
    return f"  {tokens:>5} tokens | {_format_pct(tokens, max_tokens):>5} | {name}"


def render_dry_run(all_stats: list[dict]):
    """Render dry-run output for one or more profiles."""
    all_lines = []
    for stats in all_stats:
        for part in stats["parts"]:
            for name, tokens in part["sections"]:
                all_lines.append(_format_line(tokens, stats["max_tokens"], name))
            if len(stats["parts"]) == 1:
                output_name = f"{stats['name_tmpl']}.md"
            else:
                output_name = f"{stats['name_tmpl']}_{part['part_num']}.md"
            all_lines.append(
                _format_line(part["total_tokens"], stats["max_tokens"], f"→ {output_name}")
            )

    max_width = max(len(line) for line in all_lines) if all_lines else 40
    max_width = max(max_width, 40)
    section_sep = "=" * max_width
    part_sep = "-" * max_width

    for si, stats in enumerate(all_stats):
        name = stats.get("name", "unknown")
        max_tokens = stats["max_tokens"]
        name_tmpl = stats["name_tmpl"]

        if si > 0:
            print()
        print(section_sep)
        print(f"[{name}] section".center(max_width))
        print(section_sep)

        for j, part in enumerate(stats["parts"]):
            for sec_name, tokens in part["sections"]:
                print(_format_line(tokens, max_tokens, sec_name))
            if len(stats["parts"]) == 1:
                output_name = f"{name_tmpl}.md"
            else:
                output_name = f"{name_tmpl}_{part['part_num']}.md"
            print()
            print(_format_line(part["total_tokens"], max_tokens, f"→ {output_name}"))
            if j < len(stats["parts"]) - 1:
                print(part_sep)

    print(section_sep)
