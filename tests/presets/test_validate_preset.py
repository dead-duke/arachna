"""Direct tests for _validate_preset in presets.py (v3.5.0)."""

from arachna.presets import _validate_preset


def test_validate_preset_valid():
    result = _validate_preset(
        "test",
        {
            "dirs": ["src"],
            "patterns": ["*.py"],
            "max_tokens": 100,
            "split_mode": "by_file",
        },
    )
    assert result is not None
    assert result["dirs"] == ["src"]


def test_validate_preset_not_dict():
    result = _validate_preset("bad", "string")
    assert result is None


def test_validate_preset_invalid_split_mode():
    result = _validate_preset("bad", {"split_mode": "invalid", "max_tokens": 100})
    assert result is None


def test_validate_preset_zero_max_tokens():
    result = _validate_preset("bad", {"split_mode": "by_file", "max_tokens": 0})
    assert result is None


def test_validate_preset_negative_max_tokens():
    result = _validate_preset("bad", {"split_mode": "by_file", "max_tokens": -1})
    assert result is None


def test_validate_preset_unsafe_tokenizer():
    result = _validate_preset(
        "bad",
        {
            "dirs": ["src"],
            "max_tokens": 100,
            "split_mode": "by_file",
            "tokenizer": "os:system",
        },
    )
    assert result is not None
    assert result["tokenizer"] == "default"


def test_validate_preset_safe_tokenizer():
    result = _validate_preset(
        "ok",
        {
            "dirs": ["src"],
            "max_tokens": 100,
            "split_mode": "by_file",
            "tokenizer": "tiktoken:cl100k_base",
        },
    )
    assert result is not None
    assert result["tokenizer"] == "tiktoken:cl100k_base"


def test_validate_preset_non_list_fields():
    result = _validate_preset(
        "ok",
        {
            "split_mode": "by_file",
            "max_tokens": 100,
            "dirs": "not_a_list",
            "files": 123,
        },
    )
    assert result is not None
    assert result["dirs"] == []
    assert result["files"] == []


def test_validate_preset_unknown_keys():
    result = _validate_preset(
        "ok",
        {
            "split_mode": "by_file",
            "max_tokens": 100,
            "unknown_key": "value",
        },
    )
    assert result is not None


def test_validate_preset_without_split_mode_gets_default():
    """_validate_preset uses split_mode from preset dict, default is 'by_file'."""
    result = _validate_preset("ok", {"max_tokens": 100})
    assert result is not None
    assert result.get("split_mode", "by_file") == "by_file"
