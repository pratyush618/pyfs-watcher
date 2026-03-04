"""Async wrapper for file watching."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from os import PathLike

from pyfs_watcher._core import FileChange, FileWatcher


async def async_watch(
    path: str | PathLike[str],
    *,
    recursive: bool = True,
    debounce_ms: int = 500,
    ignore_patterns: Sequence[str] | None = None,
    poll_interval_ms: int = 100,
) -> AsyncIterator[list[FileChange]]:
    """
    Async generator that yields batches of file changes.

    Usage:
        async for changes in async_watch("/path/to/dir"):
            for change in changes:
                print(change)
    """
    watcher = FileWatcher(
        str(path),
        recursive=recursive,
        debounce_ms=debounce_ms,
        ignore_patterns=list(ignore_patterns) if ignore_patterns else None,
    )
    watcher.start()
    loop = asyncio.get_running_loop()
    try:
        while True:
            events = await loop.run_in_executor(None, watcher.poll_events, poll_interval_ms)
            if events:
                yield events
    finally:
        watcher.stop()
