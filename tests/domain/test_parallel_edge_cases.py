import os

from arachna.config.profile_config import ProfileConfig
from arachna.domain.collector import collect


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


def test_parallel_workers_zero_fallback(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")
    out = tmp_path / "out"
    out.mkdir()

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "0"
    try:
        created, _, _, metrics = collect(_profile(), "P", str(out), root=tmp_path)
        assert metrics.files_read == 1
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]


def test_parallel_workers_negative_fallback(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("hello")
    out = tmp_path / "out"
    out.mkdir()

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "-1"
    try:
        created, _, _, metrics = collect(_profile(), "P", str(out), root=tmp_path)
        assert metrics.files_read == 1
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]


def test_parallel_preserves_order(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        (src / f"file_{i:02d}.py").write_text(f"# {i}")
    out = tmp_path / "out"
    out.mkdir()

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "4"
    try:
        _, _, parts, _ = collect(_profile(max_tokens=-1), "P", str(out), root=tmp_path)
        content = parts[0]
        idx_00 = content.index("file_00.py")
        idx_05 = content.index("file_05.py")
        idx_09 = content.index("file_09.py")
        assert idx_00 < idx_05 < idx_09
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]
