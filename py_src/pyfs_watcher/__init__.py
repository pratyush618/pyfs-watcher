"""pyfs_watcher - Rust-powered filesystem toolkit."""

from pyfs_watcher._core import (
    CopyError,
    # Copy/Move
    CopyProgress,
    # Dedup
    DuplicateGroup,
    FileChange,
    # Watch
    FileWatcher,
    # Exceptions
    FsWatcherError,
    HashError,
    # Hash
    HashResult,
    # Walk
    WalkEntry,
    WalkError,
    WatchError,
    copy_files,
    find_duplicates,
    hash_file,
    hash_files,
    move_files,
    walk,
    walk_collect,
)
from pyfs_watcher.watch import async_watch

__all__ = [
    # Exceptions
    "FsWatcherError",
    "WalkError",
    "HashError",
    "CopyError",
    "WatchError",
    # Walk
    "WalkEntry",
    "walk",
    "walk_collect",
    # Hash
    "HashResult",
    "hash_file",
    "hash_files",
    # Copy/Move
    "CopyProgress",
    "copy_files",
    "move_files",
    # Watch
    "FileWatcher",
    "FileChange",
    "async_watch",
    # Dedup
    "DuplicateGroup",
    "find_duplicates",
]
