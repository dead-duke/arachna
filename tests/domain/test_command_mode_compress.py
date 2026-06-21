from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.gatherer import _assemble_content
from arachna.domain.tokenization.tokenizer import count_tokens


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_paragraph",
        command="echo 'hello\n\n\n\nworld'",
        directories=[],
        patterns=[],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_command_mode_with_compress(tmp_path):
    p = _profile(compress=True)
    named_sections, parts, _indices, new_cache = _assemble_content(
        p,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )
    assert len(parts) == 1
    assert "\n\n\n\n" not in parts[0]


def test_command_mode_without_compress(tmp_path):
    p = _profile(compress=False)
    named_sections, parts, _indices, new_cache = _assemble_content(
        p,
        exclude=[],
        tokenizer=count_tokens,
        root=tmp_path,
    )
    assert len(parts) == 1
    assert "hello" in parts[0]
    assert "world" in parts[0]
