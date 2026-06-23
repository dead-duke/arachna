"""Coverage for pre_commands handling in gatherer_commands.py."""

from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.gatherer_commands import _collect_pre_commands
from arachna.domain.tokenization.tokenizer import count_tokens


def test_collect_pre_commands_empty_list(tmp_path):
    p = ProfileConfig(
        pre_commands=[],
        max_tokens=100,
        name_template="c",
    )
    result = _collect_pre_commands(p, count_tokens, root=tmp_path)
    assert result == []


def test_collect_pre_commands_no_key(tmp_path):
    p = ProfileConfig(
        directories=["src"],
        max_tokens=100,
        name_template="c",
    )
    result = _collect_pre_commands(p, count_tokens, root=tmp_path)
    assert result == []
