from pathlib import Path

import pyfs_watcher


def _create_diff_dirs(tmp_path: Path):
    src = tmp_path / "source"
    tgt = tmp_path / "target"
    src.mkdir()
    tgt.mkdir()

    # Unchanged file
    (src / "same.txt").write_text("unchanged content")
    (tgt / "same.txt").write_text("unchanged content")

    # Modified file (different content)
    (src / "modified.txt").write_text("original version")
    (tgt / "modified.txt").write_text("changed version")

    # Removed file (only in source)
    (src / "removed.txt").write_text("will be removed")

    # Added file (only in target)
    (tgt / "added.txt").write_text("new file")

    return src, tgt


def test_diff_basic(tmp_path: Path):
    src, tgt = _create_diff_dirs(tmp_path)
    result = pyfs_watcher.diff_dirs(str(src), str(tgt))

    assert len(result.added) == 1
    assert len(result.removed) == 1
    assert len(result.modified) == 1
    assert len(result.unchanged) == 1
    assert result.total_changes == 3  # added + removed + modified


def test_diff_no_content_compare(tmp_path: Path):
    src, tgt = _create_diff_dirs(tmp_path)
    result = pyfs_watcher.diff_dirs(str(src), str(tgt), compare_content=False)

    # Without content comparison, same-size files are assumed unchanged
    assert len(result.added) == 1
    assert len(result.removed) == 1


def test_diff_move_detection(tmp_path: Path):
    src = tmp_path / "source"
    tgt = tmp_path / "target"
    src.mkdir()
    tgt.mkdir()

    content = b"x" * 1000
    (src / "old_name.bin").write_bytes(content)
    (tgt / "new_name.bin").write_bytes(content)

    result = pyfs_watcher.diff_dirs(str(src), str(tgt), detect_moves=True)

    assert len(result.moved) == 1
    assert result.moved[0].source_path == "old_name.bin"
    assert result.moved[0].target_path == "new_name.bin"
    assert len(result.added) == 0
    assert len(result.removed) == 0


def test_diff_identical_dirs(tmp_path: Path):
    src = tmp_path / "source"
    tgt = tmp_path / "target"
    src.mkdir()
    tgt.mkdir()

    (src / "a.txt").write_text("same")
    (tgt / "a.txt").write_text("same")

    result = pyfs_watcher.diff_dirs(str(src), str(tgt))
    assert result.total_changes == 0
    assert len(result.unchanged) == 1


def test_diff_repr(tmp_path: Path):
    src, tgt = _create_diff_dirs(tmp_path)
    result = pyfs_watcher.diff_dirs(str(src), str(tgt))
    assert "DirDiff" in repr(result)


def test_diff_nonexistent_source(tmp_path: Path):
    import pytest

    tgt = tmp_path / "target"
    tgt.mkdir()

    with pytest.raises(pyfs_watcher.DirDiffError):
        pyfs_watcher.diff_dirs("/nonexistent/path", str(tgt))


def test_diff_skip_hidden(tmp_path: Path):
    src = tmp_path / "source"
    tgt = tmp_path / "target"
    src.mkdir()
    tgt.mkdir()

    (src / ".hidden").write_text("hidden")
    (src / "visible.txt").write_text("visible")
    (tgt / "visible.txt").write_text("visible")

    result = pyfs_watcher.diff_dirs(str(src), str(tgt), skip_hidden=True)
    # .hidden should be ignored
    assert result.total_changes == 0


def test_diff_with_sha256(tmp_path: Path):
    src, tgt = _create_diff_dirs(tmp_path)
    result = pyfs_watcher.diff_dirs(str(src), str(tgt), algorithm="sha256")
    assert len(result.added) == 1
