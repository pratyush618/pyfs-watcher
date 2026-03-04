<p align="center">
  <img src="docs/assets/logo.svg" alt="pyfs-watcher logo" width="180" />
</p>

<p align="center">
  <a href="https://pypi.org/project/pyfs_watcher/"><img src="https://img.shields.io/pypi/v/pyfs_watcher" alt="PyPI"></a>
  <a href="https://pypi.org/project/pyfs_watcher/"><img src="https://img.shields.io/pypi/pyversions/pyfs_watcher" alt="Python"></a>
  <a href="https://github.com/pratyush618/pyfs-watcher/blob/master/LICENSE"><img src="https://img.shields.io/pypi/l/pyfs_watcher" alt="License"></a>
  <a href="https://github.com/pratyush618/pyfs-watcher/actions/workflows/ci.yml"><img src="https://github.com/pratyush618/pyfs-watcher/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

# pyfs_watcher

Rust-powered filesystem toolkit for Python. Fast recursive directory listing, parallel file hashing, bulk copy/move with progress, cross-platform file watching, file deduplication, content search, directory diff/sync, snapshots, disk usage, and batch rename.

## Install

```bash
pip install pyfs_watcher
```

**From source:**

```bash
pip install maturin
maturin develop
```

## Usage

### Walk directories (parallel, faster than os.walk)

```python
import pyfs_watcher

# Streaming iterator
for entry in pyfs_watcher.walk("/data", file_type="file", glob_pattern="*.py"):
    print(entry.path, entry.file_size)

# Bulk collect (faster when you need all results)
entries = pyfs_watcher.walk_collect("/data", max_depth=3, sort=True, skip_hidden=True)
```

### Hash files (parallel SHA256/BLAKE3)

```python
# Single file
result = pyfs_watcher.hash_file("large.iso", algorithm="blake3")
print(result.hash_hex)

# Parallel batch hashing
results = pyfs_watcher.hash_files(paths, algorithm="blake3", callback=lambda r: print(r.path))
```

### Copy/move with progress

```python
def on_progress(p):
    pct = p.bytes_copied / p.total_bytes * 100
    print(f"{pct:.0f}% - {p.current_file}")

pyfs_watcher.copy_files(sources, "/dest", progress_callback=on_progress)
pyfs_watcher.move_files(sources, "/dest")  # rename if same fs, copy+delete otherwise
```

### Watch for file changes

```python
# Sync
with pyfs_watcher.FileWatcher("/data", debounce_ms=500, ignore_patterns=["*.tmp"]) as w:
    for changes in w:
        for c in changes:
            print(c.path, c.change_type)  # "created", "modified", "deleted"

# Async
async for changes in pyfs_watcher.async_watch("/data"):
    for c in changes:
        print(c.path, c.change_type)
```

### Find duplicate files

```python
groups = pyfs_watcher.find_duplicates(
    ["/photos", "/backup"],
    min_size=1024,
    progress_callback=lambda stage, done, total: print(f"{stage}: {done}/{total}"),
)
for g in groups:
    print(f"{g.file_size}B x {len(g.paths)} copies = {g.wasted_bytes}B wasted")
```

### Search file contents (parallel regex)

```python
# Find all files containing "TODO" in Python files
results = pyfs_watcher.search("/project", r"TODO", glob_pattern="*.py")
for r in results:
    for m in r.matches:
        print(f"  {r.path}:{m.line_number}: {m.line_text.strip()}")

# Streaming mode
for r in pyfs_watcher.search_iter("/project", r"FIXME"):
    print(r.path, r.match_count)
```

### Compare directories

```python
diff = pyfs_watcher.diff_dirs("/original", "/copy", detect_moves=True)
print(f"Added: {len(diff.added)}, Removed: {len(diff.removed)}, "
      f"Modified: {len(diff.modified)}, Moved: {len(diff.moved)}")
```

### Sync directories

```python
result = pyfs_watcher.sync("/source", "/backup", delete_extra=True)
print(f"Copied: {len(result.copied)}, Deleted: {len(result.deleted)}, "
      f"Skipped: {len(result.skipped)}")

# Preview changes without writing
result = pyfs_watcher.sync("/source", "/backup", dry_run=True)
```

### Snapshot and verify file integrity

```python
# Take a snapshot
snap = pyfs_watcher.snapshot("/important_data")
snap.save("baseline.json")

# Later, verify nothing changed
result = pyfs_watcher.verify("baseline.json")
if not result.ok:
    for c in result.modified:
        print(f"Modified: {c.path}")
    for c in result.removed:
        print(f"Removed: {c.path}")
```

### Disk usage

```python
usage = pyfs_watcher.disk_usage("/data")
print(f"Total: {usage.total_size:,} bytes in {usage.total_files} files")
for child in usage.children[:5]:  # top 5 largest
    print(f"  {child.path}: {child.size:,} bytes")
```

### Bulk rename

```python
# Preview renames (dry_run=True by default)
result = pyfs_watcher.bulk_rename("/photos", r"IMG_(\d+)", r"photo_\1")
for entry in result.renamed:
    print(f"  {entry.old_name} -> {entry.new_name}")

# Apply renames
result = pyfs_watcher.bulk_rename("/photos", r"IMG_(\d+)", r"photo_\1", dry_run=False)
# Undo if needed
result.undo()
```

## API

All functions raise typed exceptions inheriting from `FsWatcherError`:

- `WalkError` - directory walk failures
- `HashError` - hashing failures
- `CopyError` - copy/move failures
- `WatchError` - file watching failures
- `SearchError` - content search failures
- `DirDiffError` - directory diff failures
- `SyncError` - sync failures
- `SnapshotError` - snapshot/verify failures
- `DiskUsageError` - disk usage failures
- `RenameError` - bulk rename failures

Standard `FileNotFoundError` and `PermissionError` are raised for I/O errors.

## Development

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install maturin pytest pytest-asyncio pytest-timeout

# Build
maturin develop

# Test
cargo test        # Rust tests
pytest tests/     # Python tests

# Benchmark
python benches/bench_walk.py
python benches/bench_hash.py
```

## Tech

- Rust + PyO3 for Python bindings
- jwalk for parallel directory traversal
- BLAKE3/SHA-256 for hashing with rayon parallelism
- notify + debouncer for cross-platform file watching
- Staged dedup pipeline: size grouping -> partial hash -> full hash
- regex crate for parallel content search
- serde/serde_json for snapshot serialization
- chrono for timestamps
