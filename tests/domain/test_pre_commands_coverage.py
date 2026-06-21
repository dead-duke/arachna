"""Coverage for pre_commands handling in gatherer_core.py."""

from arachna.domain.collection.gatherer_core import _collect_pre_commands
from arachna.domain.tokenization.tokenizer import count_tokens


def test_collect_pre_commands_empty_list(tmp_path):
    result = _collect_pre_commands({"pre_commands": []}, count_tokens, root=tmp_path)
    assert result == []


def test_collect_pre_commands_no_key(tmp_path):
    result = _collect_pre_commands(
        {"directories": ["src"], "max_tokens": 100}, count_tokens, root=tmp_path
    )
    assert result == []
