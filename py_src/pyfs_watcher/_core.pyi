"""Type stubs for the Rust extension module."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from os import PathLike
from typing import (
    Callable,
    Literal,
)

# ──── Exceptions ────

class FsWatcherError(Exception):
    """Base exception for all pyfs_watcher errors."""

class WalkError(FsWatcherError):
    """Raised when a directory walk operation fails."""

class HashError(FsWatcherError):
    """Raised when a file hashing operation fails."""

class CopyError(FsWatcherError):
    """Raised when a copy or move operation fails."""

class WatchError(FsWatcherError):
    """Raised when a file watching operation fails."""

# ──── Walk ────

class WalkEntry:
    """A single entry discovered during directory traversal.

    Represents a file, directory, or symlink found by ``walk()`` or
    ``walk_collect()``.
    """

    @property
    def path(self) -> str:
        """Absolute path of the entry."""
    @property
    def is_dir(self) -> bool:
        """Whether the entry is a directory."""
    @property
    def is_file(self) -> bool:
        """Whether the entry is a regular file."""
    @property
    def is_symlink(self) -> bool:
        """Whether the entry is a symbolic link."""
    @property
    def depth(self) -> int:
        """Depth of the entry relative to the walk root (root children = 1)."""
    @property
    def file_size(self) -> int:
        """Size of the file in bytes (0 for directories)."""
    def __repr__(self) -> str: ...

class WalkIter:
    """Streaming iterator over directory entries.

    Yields ``WalkEntry`` objects as they are discovered by the parallel
    traversal engine. Supports ``Ctrl+C`` interruption.
    """

    def __iter__(self) -> Iterator[WalkEntry]: ...
    def __next__(self) -> WalkEntry: ...

def walk(
    path: str | PathLike[str],
    *,
    max_depth: int | None = None,
    follow_symlinks: bool = False,
    sort: bool = False,
    skip_hidden: bool = False,
    file_type: Literal["file", "dir", "any"] = "any",
    glob_pattern: str | None = None,
) -> WalkIter:
    """Recursively walk a directory tree, yielding entries as they are found.

    Uses parallel traversal (jwalk/rayon) for high throughput. Entries are
    streamed through an internal channel so iteration can begin before the
    full tree is scanned.

    Args:
        path: Root directory to walk.
        max_depth: Maximum recursion depth (``None`` for unlimited).
        follow_symlinks: Whether to follow symbolic links.
        sort: Sort entries by path within each directory.
        skip_hidden: Skip entries whose name starts with a dot.
        file_type: Filter by entry type — ``"file"``, ``"dir"``, or ``"any"``.
        glob_pattern: Only yield entries whose filename matches this glob
            (e.g. ``"*.py"``).

    Returns:
        A streaming iterator of ``WalkEntry`` objects.

    Raises:
        WalkError: If the root path cannot be read.

    Example::

        for entry in pyfs_watcher.walk("/data", file_type="file", glob_pattern="*.py"):
            print(entry.path, entry.file_size)
    """

def walk_collect(
    path: str | PathLike[str],
    *,
    max_depth: int | None = None,
    follow_symlinks: bool = False,
    sort: bool = False,
    skip_hidden: bool = False,
    file_type: Literal["file", "dir", "any"] = "any",
    glob_pattern: str | None = None,
) -> list[WalkEntry]:
    """Recursively walk a directory tree and return all entries at once.

    Faster than ``walk()`` when you need the full result set, because it
    avoids per-item GIL overhead by collecting everything in Rust first.

    Args:
        path: Root directory to walk.
        max_depth: Maximum recursion depth (``None`` for unlimited).
        follow_symlinks: Whether to follow symbolic links.
        sort: Sort entries by path within each directory.
        skip_hidden: Skip entries whose name starts with a dot.
        file_type: Filter by entry type — ``"file"``, ``"dir"``, or ``"any"``.
        glob_pattern: Only yield entries whose filename matches this glob
            (e.g. ``"*.py"``).

    Returns:
        A list of all matching ``WalkEntry`` objects.

    Raises:
        WalkError: If the root path cannot be read.

    Example::

        entries = pyfs_watcher.walk_collect("/data", max_depth=3, sort=True, skip_hidden=True)
        print(f"Found {len(entries)} entries")
    """

# ──── Hash ────

class HashResult:
    """Result of hashing a single file.

    Supports equality comparison and hashing based on the hex digest and
    algorithm, so instances can be used in sets and as dict keys.
    """

    @property
    def path(self) -> str:
        """Absolute path of the hashed file."""
    @property
    def hash_hex(self) -> str:
        """Hex-encoded hash digest."""
    @property
    def algorithm(self) -> str:
        """Algorithm used (``"sha256"`` or ``"blake3"``)."""
    @property
    def file_size(self) -> int:
        """Size of the file in bytes."""
    def __repr__(self) -> str: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...

def hash_file(
    path: str | PathLike[str],
    *,
    algorithm: Literal["sha256", "blake3"] = "blake3",
    chunk_size: int = 1_048_576,
) -> HashResult:
    """Hash a single file.

    Uses memory-mapped I/O for files larger than 4 MB and buffered reads
    for smaller files.

    Args:
        path: Path to the file to hash.
        algorithm: Hash algorithm — ``"blake3"`` (default, ~10x faster) or
            ``"sha256"``.
        chunk_size: Read buffer size in bytes for buffered hashing.

    Returns:
        A ``HashResult`` with the hex digest and file metadata.

    Raises:
        HashError: If hashing fails.
        FileNotFoundError: If the file does not exist.

    Example::

        result = pyfs_watcher.hash_file("large.iso", algorithm="blake3")
        print(result.hash_hex)  # "d74981efa70a0c880b..."
    """

def hash_files(
    paths: Sequence[str | PathLike[str]],
    *,
    algorithm: Literal["sha256", "blake3"] = "blake3",
    chunk_size: int = 1_048_576,
    max_workers: int | None = None,
    callback: Callable[[HashResult], None] | None = None,
) -> list[HashResult]:
    """Hash multiple files in parallel using a rayon thread pool.

    Args:
        paths: Sequence of file paths to hash.
        algorithm: Hash algorithm — ``"blake3"`` (default) or ``"sha256"``.
        chunk_size: Read buffer size in bytes for buffered hashing.
        max_workers: Maximum number of parallel threads (``None`` to use all
            available cores).
        callback: Optional function called with each ``HashResult`` as it
            completes.

    Returns:
        A list of ``HashResult`` objects (order may differ from input).

    Raises:
        HashError: If the thread pool cannot be created.

    Example::

        results = pyfs_watcher.hash_files(
            ["file1.bin", "file2.bin", "file3.bin"],
            algorithm="blake3",
            callback=lambda r: print(f"{r.path}: {r.hash_hex}"),
        )
    """

# ──── Copy / Move ────

class CopyProgress:
    """Snapshot of progress during a copy or move operation.

    Passed to the ``progress_callback`` at regular intervals.
    """

    @property
    def src(self) -> str:
        """Source base path."""
    @property
    def dst(self) -> str:
        """Destination base path."""
    @property
    def bytes_copied(self) -> int:
        """Total bytes copied so far across all files."""
    @property
    def total_bytes(self) -> int:
        """Total bytes to copy across all files."""
    @property
    def files_completed(self) -> int:
        """Number of files fully copied so far."""
    @property
    def total_files(self) -> int:
        """Total number of files to copy."""
    @property
    def current_file(self) -> str:
        """Path of the file currently being copied."""
    def __repr__(self) -> str: ...

def copy_files(
    sources: Sequence[str | PathLike[str]],
    destination: str | PathLike[str],
    *,
    overwrite: bool = False,
    preserve_metadata: bool = True,
    progress_callback: Callable[[CopyProgress], None] | None = None,
    callback_interval_ms: int = 100,
) -> list[str]:
    """Copy files and directories to a destination.

    Performs chunked I/O with optional progress reporting. Directories are
    copied recursively.

    Args:
        sources: Paths of files or directories to copy.
        destination: Target directory to copy into.
        overwrite: Whether to overwrite existing files at the destination.
        preserve_metadata: Whether to preserve file timestamps and permissions.
        progress_callback: Optional function called with a ``CopyProgress``
            snapshot at regular intervals.
        callback_interval_ms: Minimum milliseconds between progress callbacks.

    Returns:
        A list of destination paths for the copied files.

    Raises:
        CopyError: If a copy operation fails.
        FileNotFoundError: If a source path does not exist.

    Example::

        def on_progress(p):
            pct = p.bytes_copied / p.total_bytes * 100
            print(f"{pct:.0f}% - {p.current_file}")

        pyfs_watcher.copy_files(
            ["data/file1.bin", "data/file2.bin"],
            "/backup",
            progress_callback=on_progress,
        )
    """

def move_files(
    sources: Sequence[str | PathLike[str]],
    destination: str | PathLike[str],
    *,
    overwrite: bool = False,
    progress_callback: Callable[[CopyProgress], None] | None = None,
    callback_interval_ms: int = 100,
) -> list[str]:
    """Move files and directories to a destination.

    Attempts a fast rename first. Falls back to copy-then-delete when the
    source and destination are on different filesystems.

    Args:
        sources: Paths of files or directories to move.
        destination: Target directory to move into.
        overwrite: Whether to overwrite existing files at the destination.
        progress_callback: Optional function called with a ``CopyProgress``
            snapshot at regular intervals (only used during fallback copy).
        callback_interval_ms: Minimum milliseconds between progress callbacks.

    Returns:
        A list of destination paths for the moved files.

    Raises:
        CopyError: If a move operation fails.
        FileNotFoundError: If a source path does not exist.

    Example::

        pyfs_watcher.move_files(["old/data.csv", "old/report.pdf"], "/archive")
    """

# ──── Watch ────

class FileChange:
    """A single filesystem change event detected by ``FileWatcher``."""

    @property
    def path(self) -> str:
        """Absolute path of the changed file or directory."""
    @property
    def change_type(self) -> Literal["created", "modified", "deleted"]:
        """Type of change — ``"created"``, ``"modified"``, or ``"deleted"``."""
    @property
    def is_dir(self) -> bool:
        """Whether the changed path is a directory."""
    @property
    def timestamp(self) -> float:
        """Unix timestamp (seconds since epoch) when the change was detected."""
    def __repr__(self) -> str: ...

class FileWatcher:
    """Cross-platform filesystem watcher with debouncing.

    Watches a directory for file changes and delivers batched, debounced
    events. Supports both context-manager and manual start/stop usage.

    Example::

        with FileWatcher("/data", debounce_ms=500) as w:
            for changes in w:
                for c in changes:
                    print(c.path, c.change_type)
    """

    def __init__(
        self,
        path: str | PathLike[str],
        *,
        recursive: bool = True,
        debounce_ms: int = 500,
        ignore_patterns: Sequence[str] | None = None,
    ) -> None:
        """Create a new file watcher.

        Args:
            path: Directory to watch.
            recursive: Whether to watch subdirectories.
            debounce_ms: Minimum quiet time in milliseconds before delivering
                a batch of events.
            ignore_patterns: Glob patterns for paths to ignore
                (e.g. ``["*.tmp", ".git/**"]``).
        """
    def start(self) -> None:
        """Start watching for filesystem events."""
    def stop(self) -> None:
        """Stop watching and release resources."""
    def poll_events(self, timeout_ms: int = 1000) -> list[FileChange]:
        """Poll for pending events, blocking up to ``timeout_ms`` milliseconds.

        Args:
            timeout_ms: Maximum time to wait for events.

        Returns:
            A list of ``FileChange`` events (empty if the timeout expires).
        """
    def __enter__(self) -> FileWatcher: ...
    def __exit__(self, *args: object) -> None: ...
    def __iter__(self) -> Iterator[list[FileChange]]: ...
    def __next__(self) -> list[FileChange]: ...

# ──── Dedup ────

class DuplicateGroup:
    """A group of files that share identical content.

    Returned by ``find_duplicates()``. Groups are sorted by ``wasted_bytes``
    in descending order.
    """

    @property
    def hash_hex(self) -> str:
        """Hex-encoded hash digest shared by all files in the group."""
    @property
    def file_size(self) -> int:
        """Size of each file in bytes."""
    @property
    def paths(self) -> list[str]:
        """Absolute paths of the duplicate files."""
    @property
    def wasted_bytes(self) -> int:
        """Bytes wasted by duplicates (``file_size * (count - 1)``)."""
    def __repr__(self) -> str: ...
    def __len__(self) -> int:
        """Number of duplicate files in this group."""

def find_duplicates(
    paths: Sequence[str | PathLike[str]],
    *,
    recursive: bool = True,
    min_size: int = 1,
    algorithm: Literal["sha256", "blake3"] = "blake3",
    partial_hash_size: int = 4096,
    max_workers: int | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> list[DuplicateGroup]:
    """Find duplicate files using a staged pipeline.

    Efficiently identifies duplicates in three stages, each eliminating
    non-duplicates before the next expensive step:

    1. **Size grouping** — files with unique sizes are eliminated.
    2. **Partial hash** — first and last ``partial_hash_size`` bytes are
       compared.
    3. **Full hash** — remaining candidates are fully hashed to confirm.

    Args:
        paths: Directories or files to scan for duplicates.
        recursive: Whether to recurse into subdirectories.
        min_size: Ignore files smaller than this many bytes.
        algorithm: Hash algorithm — ``"blake3"`` (default) or ``"sha256"``.
        partial_hash_size: Number of bytes to read from the head and tail of
            each file during the partial-hash stage.
        max_workers: Maximum number of parallel threads (``None`` to use all
            available cores).
        progress_callback: Optional ``(stage, processed, total)`` callback
            invoked during each stage. ``stage`` is one of ``"collecting"``,
            ``"partial_hash"``, or ``"full_hash"``.

    Returns:
        A list of ``DuplicateGroup`` objects sorted by ``wasted_bytes``
        descending.

    Raises:
        HashError: If hashing fails for any file.

    Example::

        groups = pyfs_watcher.find_duplicates(
            ["/photos", "/backup"],
            min_size=1024,
            progress_callback=lambda stage, done, total: print(f"{stage}: {done}/{total}"),
        )
        for g in groups:
            print(f"{g.file_size}B x {len(g.paths)} copies = {g.wasted_bytes}B wasted")
            for path in g.paths:
                print(f"  {path}")
    """
