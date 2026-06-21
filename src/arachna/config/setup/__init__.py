"""Setup config subpackage — init (interactive/defaults) and git hook installer."""

from .hook import (
    install_hook,
)
from .init import (
    run_defaults,
    run_interactive,
)

__all__ = [
    "install_hook",
    "run_defaults",
    "run_interactive",
]
