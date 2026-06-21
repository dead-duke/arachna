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


def test_parallel_io_fallback_sequential(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(5):
        (src / f"file_{i}.py").write_text(f"# file {i}\n")

    out = tmp_path / "out"
    out.mkdir()

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "1"
    try:
        created, tokens_by_file, parts, metrics = collect(
            _profile(),
            "P",
            str(out),
            root=tmp_path,
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]

    assert len(created) >= 1
    assert metrics.files_read == 5


def test_parallel_io_with_workers(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        (src / f"file_{i}.py").write_text(f"# file {i}\n")

    out = tmp_path / "out"
    out.mkdir()

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "2"
    try:
        created, tokens_by_file, parts, metrics = collect(
            _profile(),
            "P",
            str(out),
            root=tmp_path,
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]

    assert len(created) >= 1
    assert metrics.files_read == 10


def test_parallel_io_single_file(tmp_path):
    """Single file should use sequential path even with workers > 1."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "only.py").write_text("# only\n")

    out = tmp_path / "out"
    out.mkdir()

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "4"
    try:
        created, tokens_by_file, parts, metrics = collect(
            _profile(),
            "P",
            str(out),
            root=tmp_path,
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]

    assert len(created) == 1
    assert metrics.files_read == 1


def test_parallel_io_preserves_order(tmp_path):
    """Parallel I/O must preserve file order in output."""
    src = tmp_path / "src"
    src.mkdir()
    for i in range(20):
        (src / f"file_{i:02d}.py").write_text(f"# file {i}\n")

    out = tmp_path / "out"
    out.mkdir()

    old = os.environ.get("ARACHNA_MAX_WORKERS")
    os.environ["ARACHNA_MAX_WORKERS"] = "4"
    try:
        created, tokens_by_file, parts, metrics = collect(
            _profile(max_tokens=-1),
            "P",
            str(out),
            root=tmp_path,
        )
    finally:
        if old is not None:
            os.environ["ARACHNA_MAX_WORKERS"] = old
        else:
            del os.environ["ARACHNA_MAX_WORKERS"]

    content = parts[0]
    idx_00 = content.index("file_00.py")
    idx_10 = content.index("file_10.py")
    idx_19 = content.index("file_19.py")
    assert idx_00 < idx_10 < idx_19
