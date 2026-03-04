---
hide:
  - navigation
---

[![PyPI](https://img.shields.io/pypi/v/pyfs_watcher)](https://pypi.org/project/pyfs_watcher/)
[![Python](https://img.shields.io/pypi/pyversions/pyfs_watcher)](https://pypi.org/project/pyfs_watcher/)
[![License](https://img.shields.io/pypi/l/pyfs_watcher)](https://github.com/pratyush618/pyfs-watcher/blob/master/LICENSE)
[![CI](https://github.com/pratyush618/pyfs-watcher/actions/workflows/ci.yml/badge.svg)](https://github.com/pratyush618/pyfs-watcher/actions/workflows/ci.yml)

**Rust-powered filesystem toolkit for Python.**

Fast recursive directory listing, parallel file hashing, bulk copy/move with progress, cross-platform file watching, file deduplication, content search, directory diff and sync, file integrity snapshots, disk usage analysis, and batch rename — all from a single, typed Python package.

---

## Why pyfs-watcher?

- **Performance** — Core operations run in Rust with parallel execution via Rayon, bypassing the GIL. Walk directories and hash files 10x faster than pure Python.
- **Type Safety** — Full type stubs (`py.typed`) ship with the package. Every function, class, and parameter has type annotations for IDE autocompletion and mypy/pyright checking.
- **Cross-Platform** — Works on Linux, macOS, and Windows. File watching uses native OS APIs (inotify, FSEvents, ReadDirectoryChangesW).
- **Batteries Included** — Eleven feature modules cover the most common filesystem operations: walk, hash, copy/move, watch, dedup, search, diff, sync, snapshot, disk usage, and rename.

---

## Features

<div class="grid cards" markdown>

- **Walk**

    ---

    Parallel recursive directory traversal powered by jwalk. Stream entries one-by-one or collect them all at once.

    [Walk guide →](guides/walk.md)

- **Hash**

    ---

    BLAKE3 and SHA-256 hashing with automatic memory-mapped I/O for large files. Parallel batch hashing across all cores.

    [Hash guide →](guides/hash.md)

- **Copy / Move**

    ---

    Bulk file copy and move with real-time progress callbacks. Smart cross-device move with automatic fallback.

    [Copy/Move guide →](guides/copy-move.md)

- **Watch**

    ---

    Cross-platform filesystem watcher with debouncing. Supports both synchronous iteration and async generators.

    [Watch guide →](guides/watch.md)

- **Dedup**

    ---

    Three-stage duplicate finder: size grouping, partial hash, then full hash. Finds duplicates across multiple directories.

    [Dedup guide →](guides/dedup.md)

- **Search**

    ---

    Parallel content search with regex patterns. Skips binary files, supports context lines, streaming and collect modes.

    [Search guide →](guides/search.md)

- **Diff**

    ---

    Compare two directories to find added, removed, modified, and moved files. Content-aware with optional move detection.

    [Diff guide →](guides/diff.md)

- **Sync**

    ---

    Incremental directory sync with dry-run preview, delete-extra support, and progress callbacks. Only copies what changed.

    [Sync guide →](guides/sync.md)

- **Snapshot**

    ---

    Capture file hashes and metadata to JSON. Verify later to detect additions, removals, and modifications.

    [Snapshot guide →](guides/snapshot.md)

- **Disk Usage**

    ---

    Parallel directory size calculation with per-child breakdown, sorted by size. Faster than `du`.

    [Disk Usage guide →](guides/disk-usage.md)

- **Rename**

    ---

    Regex-based batch file rename with dry-run preview and undo support. Safe by default.

    [Rename guide →](guides/rename.md)

</div>

---

## Quick Install

```bash
pip install pyfs_watcher
```

---

## At a Glance

=== "Walk"

    ```python
    import pyfs_watcher

    for entry in pyfs_watcher.walk("/data", file_type="file", glob_pattern="*.py"):
        print(entry.path, entry.file_size)
    ```

=== "Hash"

    ```python
    result = pyfs_watcher.hash_file("large.iso", algorithm="blake3")
    print(result.hash_hex)
    ```

=== "Copy/Move"

    ```python
    pyfs_watcher.copy_files(
        ["src/a.bin", "src/b.bin"], "/backup",
        progress_callback=lambda p: print(f"{p.bytes_copied / p.total_bytes:.0%}"),
    )
    ```

=== "Watch"

    ```python
    with pyfs_watcher.FileWatcher("/data", debounce_ms=500) as w:
        for changes in w:
            for c in changes:
                print(c.path, c.change_type)
    ```

=== "Dedup"

    ```python
    groups = pyfs_watcher.find_duplicates(["/photos", "/backup"], min_size=1024)
    for g in groups:
        print(f"{g.file_size}B x {len(g.paths)} copies")
    ```

=== "Search"

    ```python
    results = pyfs_watcher.search("/project", r"TODO", glob_pattern="*.py")
    for r in results:
        for m in r.matches:
            print(f"{r.path}:{m.line_number}: {m.line_text.strip()}")
    ```

=== "Diff"

    ```python
    diff = pyfs_watcher.diff_dirs("/original", "/copy", detect_moves=True)
    print(f"Added: {len(diff.added)}, Modified: {len(diff.modified)}")
    ```

=== "Sync"

    ```python
    result = pyfs_watcher.sync("/source", "/backup", delete_extra=True)
    print(f"Copied: {len(result.copied)}, Deleted: {len(result.deleted)}")
    ```

=== "Snapshot"

    ```python
    snap = pyfs_watcher.snapshot("/important_data")
    snap.save("baseline.json")
    result = pyfs_watcher.verify("baseline.json")
    print("OK" if result.ok else "Changes detected!")
    ```

=== "Disk Usage"

    ```python
    usage = pyfs_watcher.disk_usage("/data")
    for child in usage.children[:5]:
        print(f"{child.path}: {child.size:,} bytes")
    ```

=== "Rename"

    ```python
    result = pyfs_watcher.bulk_rename("/photos", r"IMG_(\d+)", r"photo_\1")
    for entry in result.renamed:
        print(f"{entry.old_name} -> {entry.new_name}")
    ```

---

[Get Started →](getting-started.md){ .md-button .md-button--primary }
[API Reference](api/index.md){ .md-button }
