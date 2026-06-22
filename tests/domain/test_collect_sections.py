import os

from arachna.config.profile_config import ProfileConfig
from arachna.domain.collection.gatherer_files import _collect_named_sections
from arachna.domain.tokenization.tokenizer import count_tokens


def _profile(**overrides):
    p = ProfileConfig(
        name_template="c",
        title_template="# T (part {part})\n\n",
        max_tokens=16000,
        split_mode="by_file",
        directories=[str],
        patterns=["*.py"],
        use_gitignore=False,
    )
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def test_collect_sections_incremental_new_files(tmp_path):
    (tmp_path / "a.py").write_text("new file")
    p = _profile(directories=[str(tmp_path)])
    sections, cache = _collect_named_sections(
        p,
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache={},
        root=tmp_path,
    )
    assert len(sections) == 1
    assert len(cache) > 0


def test_collect_sections_incremental_skips_unchanged(tmp_path):
    (tmp_path / "a.py").write_text("unchanged")
    p = _profile(directories=[str(tmp_path)])
    sections1, cache = _collect_named_sections(
        p,
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache={},
        root=tmp_path,
    )
    assert len(sections1) == 1

    sections2, cache2 = _collect_named_sections(
        p,
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache=cache,
        root=tmp_path,
    )
    assert len(sections2) == 0


def test_collect_sections_incremental_detects_modified(tmp_path):
    fp = tmp_path / "a.py"
    fp.write_text("original")
    p = _profile(directories=[str(tmp_path)])
    sections1, cache = _collect_named_sections(
        p,
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache={},
        root=tmp_path,
    )
    assert len(sections1) == 1

    fp.write_text("modified")
    st = fp.stat()
    os.utime(str(fp), ns=(st.st_atime_ns, st.st_mtime_ns - 10_000_000_000))

    sections2, cache2 = _collect_named_sections(
        p,
        exclude=[],
        tokenizer=count_tokens,
        incremental=True,
        cache=cache,
        root=tmp_path,
    )
    assert len(sections2) == 1
