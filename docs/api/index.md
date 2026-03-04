# API Reference

Complete reference for all public symbols exported by `pyfs_watcher`.

## Summary

| Symbol | Category | Description |
|---|---|---|
| [`walk()`](walk.md#walk) | Walk | Streaming directory traversal |
| [`walk_collect()`](walk.md#walk_collect) | Walk | Collect all entries at once |
| [`WalkEntry`](walk.md#walkentry) | Walk | Single directory entry |
| [`WalkIter`](walk.md#walkiter) | Walk | Streaming walk iterator |
| [`hash_file()`](hash.md#hash_file) | Hash | Hash a single file |
| [`hash_files()`](hash.md#hash_files) | Hash | Hash multiple files in parallel |
| [`HashResult`](hash.md#hashresult) | Hash | Hash result with metadata |
| [`copy_files()`](copy.md#copy_files) | Copy/Move | Copy files with progress |
| [`move_files()`](copy.md#move_files) | Copy/Move | Move files with smart fallback |
| [`CopyProgress`](copy.md#copyprogress) | Copy/Move | Progress snapshot |
| [`FileWatcher`](watch.md#filewatcher) | Watch | Filesystem watcher |
| [`FileChange`](watch.md#filechange) | Watch | Single change event |
| [`async_watch()`](watch.md#async_watch) | Watch | Async watch generator |
| [`find_duplicates()`](dedup.md#find_duplicates) | Dedup | Find duplicate files |
| [`DuplicateGroup`](dedup.md#duplicategroup) | Dedup | Group of duplicate files |
| [`search()`](search.md#search) | Search | Parallel content search |
| [`search_iter()`](search.md#search_iter) | Search | Streaming content search |
| [`SearchResult`](search.md#searchresult) | Search | Matches in a single file |
| [`SearchMatch`](search.md#searchmatch) | Search | Single line match |
| [`SearchIter`](search.md#searchiter) | Search | Streaming search iterator |
| [`diff_dirs()`](diff.md#diff_dirs) | Diff | Compare two directories |
| [`DirDiff`](diff.md#dirdiff) | Diff | Comparison result |
| [`DiffEntry`](diff.md#diffentry) | Diff | Single differing file |
| [`MovedEntry`](diff.md#movedentry) | Diff | Detected moved file |
| [`sync()`](sync.md#sync) | Sync | Incremental directory sync |
| [`SyncResult`](sync.md#syncresult) | Sync | Sync operation result |
| [`SyncProgress`](sync.md#syncprogress) | Sync | Sync progress snapshot |
| [`SyncFileError`](sync.md#syncfileerror) | Sync | Per-file sync error |
| [`snapshot()`](snapshot.md#snapshot) | Snapshot | Create filesystem snapshot |
| [`verify()`](snapshot.md#verify) | Snapshot | Verify snapshot integrity |
| [`Snapshot`](snapshot.md#snapshot-class) | Snapshot | Snapshot object |
| [`SnapshotEntry`](snapshot.md#snapshotentry) | Snapshot | Single snapshot entry |
| [`VerifyResult`](snapshot.md#verifyresult) | Snapshot | Verification result |
| [`VerifyChange`](snapshot.md#verifychange) | Snapshot | Single detected change |
| [`disk_usage()`](disk-usage.md#disk_usage) | Disk Usage | Parallel size calculation |
| [`DiskUsage`](disk-usage.md#diskusage) | Disk Usage | Usage result |
| [`DiskUsageEntry`](disk-usage.md#diskusageentry) | Disk Usage | Per-child breakdown |
| [`bulk_rename()`](rename.md#bulk_rename) | Rename | Regex-based batch rename |
| [`RenameResult`](rename.md#renameresult) | Rename | Rename operation result |
| [`RenameEntry`](rename.md#renameentry) | Rename | Single rename mapping |
| [`RenameFileError`](rename.md#renamefileerror) | Rename | Per-file rename error |

## Exceptions

| Exception | Description |
|---|---|
| [`FsWatcherError`](exceptions.md#fswatchererror) | Base exception for all errors |
| [`WalkError`](exceptions.md#walkerror) | Directory walk failure |
| [`HashError`](exceptions.md#hasherror) | Hashing failure |
| [`CopyError`](exceptions.md#copyerror) | Copy/move failure |
| [`WatchError`](exceptions.md#watcherror) | File watching failure |
| [`SearchError`](exceptions.md#searcherror) | Content search failure |
| [`DirDiffError`](exceptions.md#dirdifferror) | Directory diff failure |
| [`SyncError`](exceptions.md#syncerror) | Sync failure |
| [`SnapshotError`](exceptions.md#snapshoterror) | Snapshot/verify failure |
| [`DiskUsageError`](exceptions.md#diskusageerror) | Disk usage failure |
| [`RenameError`](exceptions.md#renameerror) | Bulk rename failure |

## Import

Functions and the `FileWatcher` class are available from the top-level package:

```python
from pyfs_watcher import (
    walk, walk_collect, hash_file, hash_files,
    copy_files, move_files, FileWatcher, async_watch,
    find_duplicates, search, search_iter, diff_dirs,
    sync, snapshot, verify, disk_usage, bulk_rename,
)
```

Data classes and result types live in `pyfs_watcher.types`:

```python
from pyfs_watcher.types import (
    WalkEntry, HashResult, CopyProgress, FileChange,
    DuplicateGroup, SearchResult, SearchMatch, SearchIter,
    DirDiff, DiffEntry, MovedEntry,
    SyncResult, SyncProgress, SyncFileError,
    Snapshot, SnapshotEntry, VerifyResult, VerifyChange,
    DiskUsage, DiskUsageEntry,
    RenameResult, RenameEntry, RenameFileError,
)
```

Exceptions live in `pyfs_watcher.errors`:

```python
from pyfs_watcher.errors import (
    FsWatcherError, WalkError, HashError, CopyError, WatchError,
    SearchError, DirDiffError, SyncError, SnapshotError, DiskUsageError, RenameError,
)
```
