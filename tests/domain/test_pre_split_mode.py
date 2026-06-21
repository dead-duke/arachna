from arachna.config.profile_config import ProfileConfig
from arachna.domain.gatherer import _assemble_content
from arachna.domain.tokenizer import count_tokens


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=["src"],
        patterns=["*.py"],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_unified_split_pre_commands_and_files_together(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")
    (src / "utils.py").write_text("def foo(): pass")

    p = _profile(pre_commands=["echo '=== SECTION ==='", "echo 'another section'"])

    named_sections, parts, _indices, new_cache = _assemble_content(
        p,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(named_sections) >= 4
    assert len(parts) == 1


def test_unified_split_small_limit_many_parts(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("x" * 500)
    (src / "b.py").write_text("y" * 500)

    p = _profile(pre_commands=["echo 'hello'"], max_tokens=10)

    named_sections, parts, _indices, new_cache = _assemble_content(
        p,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 3


def test_unified_split_with_compress(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hi')")

    p = _profile(pre_commands=["echo 'line1\n\n\n\nline2'"], compress=True)

    named_sections, parts, _indices, new_cache = _assemble_content(
        p,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 1
    for part in parts:
        assert "\n\n\n\n" not in part


def test_unified_split_without_pre_commands(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("print('hello')")

    p = _profile()

    named_sections, parts, _indices, new_cache = _assemble_content(
        p,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) == 1


def test_unified_split_dense_packing(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(20):
        (src / f"file_{i}.py").write_text("x" * 1000)

    max_tok = 2000
    p = _profile(pre_commands=["echo 'git log output'"], max_tokens=max_tok)

    named_sections, parts, _indices, new_cache = _assemble_content(
        p,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )

    assert len(parts) >= 2, f"Expected >= 2 parts, got {len(parts)}"
    for i, part in enumerate(parts[:-1]):
        part_tokens = count_tokens(part)
        assert part_tokens >= max_tok * 0.5, (
            f"Part {i} has {part_tokens} tokens, expected >= {max_tok * 0.5}"
        )
