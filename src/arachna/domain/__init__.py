"""Domain layer — pure data transformations, no I/O dependencies.

Subpackages:
- cache: incremental collection file modification cache
- collection: content gathering, command execution, mode strategies
- formatting: file formatting, language detection, headers, binary handling
- tokenization: token counting, language dispatch for parsing
- execution: command running, content splitting, gitignore parsing
"""

from .api_types import (
    CollectResult,
    DiffResult,
    DiffSection,
    DiffStats,
    GCResult,
    PipelineMetrics,
    SnapshotInfo,
    StoreStats,
)
from .atomic_write import (
    atomic_write_bytes,
    atomic_write_text,
)
from .cache import (
    get_changed_files,
    load_cache,
    save_cache,
    update_cache,
)
from .collection import (
    clean_manifest,
    collect,
    dry_run,
    gather_command,
    gather_files,
    load_manifest,
    save_manifest,
)
from .collection.gatherer_files import _scan_directories as scan_directories
from .compressor import (
    compress,
    estimate_savings,
)
from .differ_stats import (
    compute_diff_stats,
)
from .execution import (
    extract_signatures,
    load_gitignore_patterns,
    pack_into_parts,
    run_command,
    run_pre_commands,
    split,
    split_sections,
)
from .formatting.formatter import (
    C_LIKE_LANGS,
    SCRIPT_LANGS,
    format_file_section,
    is_excluded,
    lang_for_path,
)
from .interfaces import (
    Tokenizer,
)
from .path_utils import (
    SafePath,
    validate_path,
)
from .tokenization import (
    RegexTimeoutError,
    count_tokens,
    get_block_parser,
    get_header_parser,
    load_tokenizer,
)

__all__ = [
    "C_LIKE_LANGS",
    "CollectResult",
    "DiffResult",
    "DiffSection",
    "DiffStats",
    "GCResult",
    "PipelineMetrics",
    "RegexTimeoutError",
    "SCRIPT_LANGS",
    "SafePath",
    "SnapshotInfo",
    "StoreStats",
    "Tokenizer",
    "atomic_write_bytes",
    "atomic_write_text",
    "clean_manifest",
    "collect",
    "compress",
    "compute_diff_stats",
    "count_tokens",
    "dry_run",
    "estimate_savings",
    "extract_signatures",
    "format_file_section",
    "gather_command",
    "gather_files",
    "get_block_parser",
    "get_changed_files",
    "get_header_parser",
    "is_excluded",
    "lang_for_path",
    "load_cache",
    "load_gitignore_patterns",
    "load_manifest",
    "load_tokenizer",
    "pack_into_parts",
    "run_command",
    "run_pre_commands",
    "save_cache",
    "save_manifest",
    "scan_directories",
    "split",
    "split_sections",
    "update_cache",
    "validate_path",
]
