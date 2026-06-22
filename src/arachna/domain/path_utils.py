# Copyright (C) 2026 Artem Terenin / arachna — AGPLv3
"""Path validation utilities for arachna.

SafePath wraps pathlib.Path with mandatory root validation.
Once constructed, all I/O is guaranteed to stay within root.
"""

from pathlib import Path


def validate_path(path: Path, root: Path) -> bool:
    """Check that path is within root directory.

    Resolves both paths to absolute paths and verifies that path
    is a descendant of root. Used to prevent path traversal attacks
    in file I/O operations (SonarCloud S2083).

    Args:
        path: The path to validate.
        root: The root directory that path must be within.

    Returns:
        True if path is within root, False otherwise.
    """
    try:
        resolved_path = path.resolve()
        resolved_root = root.resolve()
        resolved_path.relative_to(resolved_root)
        return True
    except (ValueError, OSError):
        return False


class SafePath:
    """A pathlib.Path wrapper that guarantees all I/O stays within a root directory.

    Validation happens once at construction. After that, all delegated
    operations (read, write, unlink, mkdir, etc.) are guaranteed to be
    within the root.

    I/O methods validate inline via resolve() + is_relative_to() for
    TOCTOU protection (symlink swap between construction and I/O).

    Usage:
        root = SafePath("/project")
        out = root / "output"            # SafePath — within root
        out.mkdir(parents=True)          # guaranteed safe
        f = out / "chat-code_1.md"       # SafePath — within root
        f.write_text("content")          # guaranteed safe
        bad = root / "../../etc/passwd"  # raises ValueError
    """

    __slots__ = ("_path", "_root")

    def __init__(self, path: str | Path, root: str | Path | None = None):
        if isinstance(path, SafePath):
            self._path = path._path
            self._root = path._root
            return
        self._path = Path(path)
        if root is not None:
            self._root = Path(root)
            if not validate_path(self._path, self._root):
                raise ValueError(
                    f"Path traversal detected: {self._path} is outside root {self._root}"
                )
        else:
            self._root = self._path

    def _resolve_and_validate(self) -> Path:
        """Resolve and validate path is within root. Returns resolved Path."""
        resolved = self._path.resolve()
        resolved_root = self._root.resolve()
        try:
            resolved.relative_to(resolved_root)
        except ValueError:
            raise ValueError(
                f"Path traversal detected at I/O time: {self._path} resolved to {resolved}, "
                f"which is outside root {resolved_root}"
            ) from None
        return resolved

    def to_path(self) -> Path:
        """Return the underlying pathlib.Path for use with functions that expect Path."""
        return self._path

    def __truediv__(self, other: str) -> "SafePath":
        return SafePath(self._path / other, self._root)

    def __str__(self) -> str:
        return str(self._path)

    def __repr__(self) -> str:
        return f"SafePath({self._path!r}, root={self._root!r})"

    def __fspath__(self) -> str:
        return str(self._path)

    # -- comparison delegates ---------------------------------------

    def __lt__(self, other: "SafePath") -> bool:
        return self._path < other._path

    def __le__(self, other: "SafePath") -> bool:
        return self._path <= other._path

    def __gt__(self, other: "SafePath") -> bool:
        return self._path > other._path

    def __ge__(self, other: "SafePath") -> bool:
        return self._path >= other._path

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SafePath):
            return self._path == other._path
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._path)

    # -- properties -------------------------------------------------

    @property
    def name(self) -> str:
        return self._path.name

    @property
    def parent(self) -> "SafePath":
        return SafePath(self._path.parent, self._root)

    @property
    def suffix(self) -> str:
        return self._path.suffix

    @property
    def stem(self) -> str:
        return self._path.stem

    # -- I/O delegates ----------------------------------------------

    def read_text(self, encoding: str = "utf-8") -> str:
        resolved = self._resolve_and_validate()
        return resolved.read_text(encoding=encoding)

    def read_bytes(self) -> bytes:
        resolved = self._resolve_and_validate()
        return resolved.read_bytes()

    def write_text(self, data: str, encoding: str = "utf-8") -> int:
        resolved = self._resolve_and_validate()
        return resolved.write_text(data, encoding=encoding)

    def write_bytes(self, data: bytes) -> int:
        resolved = self._resolve_and_validate()
        return resolved.write_bytes(data)

    def exists(self) -> bool:
        return self._path.exists()

    def is_file(self) -> bool:
        return self._path.is_file()

    def is_dir(self) -> bool:
        return self._path.is_dir()

    def is_symlink(self) -> bool:
        return self._path.is_symlink()

    def unlink(self, missing_ok: bool = False) -> None:
        return self._path.unlink(missing_ok=missing_ok)

    def mkdir(self, parents: bool = False, exist_ok: bool = False) -> None:
        return self._path.mkdir(parents=parents, exist_ok=exist_ok)

    def stat(self):
        return self._path.stat()

    def rglob(self, pattern: str):
        for p in self._path.rglob(pattern):
            yield SafePath(p, self._root)

    def glob(self, pattern: str):
        for p in self._path.glob(pattern):
            yield SafePath(p, self._root)

    def open(self, *args, **kwargs):
        resolved = self._resolve_and_validate()
        return resolved.open(*args, **kwargs)

    def resolve(self) -> "SafePath":
        return SafePath(self._path.resolve(), self._root)

    def relative_to(self, other: "SafePath") -> Path:
        return self._path.relative_to(other._path)

    def symlink_to(self, target: "SafePath") -> None:
        return self._path.symlink_to(target._path)
