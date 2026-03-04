use std::collections::HashMap;
use std::path::PathBuf;

use pyo3::prelude::*;
use rayon::prelude::*;

use crate::errors::FsError;
use crate::hash::{self, Algorithm};
use crate::utils::WalkFilter;

/// A file that differs between source and target.
#[pyclass(frozen)]
#[derive(Clone)]
pub struct DiffEntry {
    #[pyo3(get)]
    pub path: String,
    #[pyo3(get)]
    pub source_size: Option<u64>,
    #[pyo3(get)]
    pub target_size: Option<u64>,
    #[pyo3(get)]
    pub source_hash: Option<String>,
    #[pyo3(get)]
    pub target_hash: Option<String>,
}

#[pymethods]
impl DiffEntry {
    fn __repr__(&self) -> String {
        format!("DiffEntry({:?})", self.path)
    }
}

/// A file detected as moved (same content, different path).
#[pyclass(frozen)]
#[derive(Clone)]
pub struct MovedEntry {
    #[pyo3(get)]
    pub source_path: String,
    #[pyo3(get)]
    pub target_path: String,
    #[pyo3(get)]
    pub hash_hex: String,
    #[pyo3(get)]
    pub file_size: u64,
}

#[pymethods]
impl MovedEntry {
    fn __repr__(&self) -> String {
        format!(
            "MovedEntry({:?} -> {:?})",
            self.source_path, self.target_path
        )
    }
}

/// Result of comparing two directories.
#[pyclass(frozen)]
#[derive(Clone)]
pub struct DirDiff {
    #[pyo3(get)]
    pub added: Vec<DiffEntry>,
    #[pyo3(get)]
    pub removed: Vec<DiffEntry>,
    #[pyo3(get)]
    pub modified: Vec<DiffEntry>,
    #[pyo3(get)]
    pub unchanged: Vec<DiffEntry>,
    #[pyo3(get)]
    pub moved: Vec<MovedEntry>,
}

#[pymethods]
impl DirDiff {
    #[getter]
    fn total_changes(&self) -> usize {
        self.added.len() + self.removed.len() + self.modified.len() + self.moved.len()
    }

    fn __repr__(&self) -> String {
        format!(
            "DirDiff(added={}, removed={}, modified={}, unchanged={}, moved={})",
            self.added.len(),
            self.removed.len(),
            self.modified.len(),
            self.unchanged.len(),
            self.moved.len()
        )
    }
}

struct FileInfo {
    abs_path: PathBuf,
    size: u64,
}

/// Compare two directories and return their differences.
#[pyfunction]
#[pyo3(signature = (source, target, *, algorithm="blake3", compare_content=true,
                     skip_hidden=false, glob_pattern=None, max_depth=None,
                     detect_moves=false, max_workers=None, progress_callback=None))]
#[allow(clippy::too_many_arguments)]
pub fn diff_dirs(
    py: Python<'_>,
    source: &str,
    target: &str,
    algorithm: &str,
    compare_content: bool,
    skip_hidden: bool,
    glob_pattern: Option<&str>,
    max_depth: Option<usize>,
    detect_moves: bool,
    max_workers: Option<usize>,
    progress_callback: Option<PyObject>,
) -> PyResult<DirDiff> {
    let src_root = PathBuf::from(source);
    let tgt_root = PathBuf::from(target);

    if !src_root.is_dir() {
        return Err(FsError::DirDiff(format!("source is not a directory: {}", source)).into());
    }
    if !tgt_root.is_dir() {
        return Err(FsError::DirDiff(format!("target is not a directory: {}", target)).into());
    }

    let algo = Algorithm::from_str(algorithm)?;

    let filter = WalkFilter::from_options(
        skip_hidden,
        glob_pattern,
        max_depth,
        false,
        FsError::DirDiff,
    )?;

    // Report walking progress
    report_stage(py, &progress_callback, "walking_source")?;

    let src_files = py.allow_threads(|| crate::utils::walk_files_filtered(&src_root, &filter));
    let src_map: HashMap<String, FileInfo> = src_files
        .into_iter()
        .map(|(rel, abs, size)| {
            (
                rel,
                FileInfo {
                    abs_path: abs,
                    size,
                },
            )
        })
        .collect();

    report_stage(py, &progress_callback, "walking_target")?;

    let tgt_files = py.allow_threads(|| crate::utils::walk_files_filtered(&tgt_root, &filter));
    let tgt_map: HashMap<String, FileInfo> = tgt_files
        .into_iter()
        .map(|(rel, abs, size)| {
            (
                rel,
                FileInfo {
                    abs_path: abs,
                    size,
                },
            )
        })
        .collect();

    report_stage(py, &progress_callback, "comparing")?;

    let result = py.allow_threads(|| {
        compare_maps(
            &src_map,
            &tgt_map,
            algo,
            compare_content,
            detect_moves,
            max_workers,
        )
    });

    Ok(result)
}

fn report_stage(py: Python<'_>, callback: &Option<PyObject>, stage: &str) -> PyResult<()> {
    py.check_signals()?;
    if let Some(ref cb) = callback {
        cb.call1(py, (stage,))?;
    }
    Ok(())
}

fn compare_maps(
    src_map: &HashMap<String, FileInfo>,
    tgt_map: &HashMap<String, FileInfo>,
    algo: Algorithm,
    compare_content: bool,
    detect_moves: bool,
    max_workers: Option<usize>,
) -> DirDiff {
    let mut added = Vec::new();
    let mut removed = Vec::new();
    let mut modified = Vec::new();
    let mut unchanged = Vec::new();

    // Files to hash for content comparison
    let mut to_hash: Vec<(&str, &PathBuf, &PathBuf, u64, u64)> = Vec::new();

    // Check source files against target
    for (rel_path, src_info) in src_map {
        match tgt_map.get(rel_path) {
            None => {
                removed.push(DiffEntry {
                    path: rel_path.clone(),
                    source_size: Some(src_info.size),
                    target_size: None,
                    source_hash: None,
                    target_hash: None,
                });
            }
            Some(tgt_info) => {
                if src_info.size != tgt_info.size {
                    // Different sizes = definitely modified
                    modified.push(DiffEntry {
                        path: rel_path.clone(),
                        source_size: Some(src_info.size),
                        target_size: Some(tgt_info.size),
                        source_hash: None,
                        target_hash: None,
                    });
                } else if compare_content {
                    // Same size — need hash comparison
                    to_hash.push((
                        rel_path.as_str(),
                        &src_info.abs_path,
                        &tgt_info.abs_path,
                        src_info.size,
                        tgt_info.size,
                    ));
                } else {
                    unchanged.push(DiffEntry {
                        path: rel_path.clone(),
                        source_size: Some(src_info.size),
                        target_size: Some(tgt_info.size),
                        source_hash: None,
                        target_hash: None,
                    });
                }
            }
        }
    }

    // Files only in target
    for (rel_path, tgt_info) in tgt_map {
        if !src_map.contains_key(rel_path) {
            added.push(DiffEntry {
                path: rel_path.clone(),
                source_size: None,
                target_size: Some(tgt_info.size),
                source_hash: None,
                target_hash: None,
            });
        }
    }

    // Hash same-size files for content comparison
    if !to_hash.is_empty() {
        let hash_fn = || -> Vec<(String, Option<String>, Option<String>, bool)> {
            to_hash
                .par_iter()
                .map(|(rel, src_path, tgt_path, _, _)| {
                    let src_hash = hash::hash_file_internal(src_path, algo, 1_048_576)
                        .ok()
                        .map(|r| r.hash_hex);
                    let tgt_hash = hash::hash_file_internal(tgt_path, algo, 1_048_576)
                        .ok()
                        .map(|r| r.hash_hex);
                    let same = src_hash == tgt_hash;
                    (rel.to_string(), src_hash, tgt_hash, same)
                })
                .collect()
        };

        let hash_results = if let Some(workers) = max_workers {
            if let Ok(pool) = rayon::ThreadPoolBuilder::new().num_threads(workers).build() {
                pool.install(hash_fn)
            } else {
                hash_fn()
            }
        } else {
            hash_fn()
        };

        for (rel, src_hash, tgt_hash, same) in hash_results {
            let src_info = src_map.get(&rel).unwrap();
            let tgt_info = tgt_map.get(&rel).unwrap();
            if same {
                unchanged.push(DiffEntry {
                    path: rel,
                    source_size: Some(src_info.size),
                    target_size: Some(tgt_info.size),
                    source_hash: src_hash,
                    target_hash: tgt_hash,
                });
            } else {
                modified.push(DiffEntry {
                    path: rel,
                    source_size: Some(src_info.size),
                    target_size: Some(tgt_info.size),
                    source_hash: src_hash,
                    target_hash: tgt_hash,
                });
            }
        }
    }

    // Move detection
    let moved = if detect_moves && (!removed.is_empty() && !added.is_empty()) {
        detect_moved_files(&removed, &added, src_map, tgt_map, algo, max_workers)
    } else {
        Vec::new()
    };

    // Remove moved files from added/removed
    if !moved.is_empty() {
        let moved_src: std::collections::HashSet<&str> =
            moved.iter().map(|m| m.source_path.as_str()).collect();
        let moved_tgt: std::collections::HashSet<&str> =
            moved.iter().map(|m| m.target_path.as_str()).collect();

        removed.retain(|e| !moved_src.contains(e.path.as_str()));
        added.retain(|e| !moved_tgt.contains(e.path.as_str()));
    }

    DirDiff {
        added,
        removed,
        modified,
        unchanged,
        moved,
    }
}

fn detect_moved_files(
    removed: &[DiffEntry],
    added: &[DiffEntry],
    src_map: &HashMap<String, FileInfo>,
    tgt_map: &HashMap<String, FileInfo>,
    algo: Algorithm,
    max_workers: Option<usize>,
) -> Vec<MovedEntry> {
    // Hash removed files
    let removed_paths: Vec<(&str, &PathBuf, u64)> = removed
        .iter()
        .filter_map(|e| {
            src_map
                .get(&e.path)
                .map(|info| (e.path.as_str(), &info.abs_path, info.size))
        })
        .collect();

    let added_paths: Vec<(&str, &PathBuf, u64)> = added
        .iter()
        .filter_map(|e| {
            tgt_map
                .get(&e.path)
                .map(|info| (e.path.as_str(), &info.abs_path, info.size))
        })
        .collect();

    let hash_paths = |paths: &[(&str, &PathBuf, u64)]| -> Vec<(String, String, u64)> {
        paths
            .par_iter()
            .filter_map(|(rel, abs, size)| {
                hash::hash_file_internal(abs, algo, 1_048_576)
                    .ok()
                    .map(|r| (rel.to_string(), r.hash_hex, *size))
            })
            .collect()
    };

    let (removed_hashes, added_hashes) = if let Some(workers) = max_workers {
        if let Ok(pool) = rayon::ThreadPoolBuilder::new().num_threads(workers).build() {
            pool.install(|| (hash_paths(&removed_paths), hash_paths(&added_paths)))
        } else {
            (hash_paths(&removed_paths), hash_paths(&added_paths))
        }
    } else {
        (hash_paths(&removed_paths), hash_paths(&added_paths))
    };

    // Build hash -> path map for added files
    let mut added_by_hash: HashMap<String, Vec<(String, u64)>> = HashMap::new();
    for (rel, hash, size) in added_hashes {
        added_by_hash.entry(hash).or_default().push((rel, size));
    }

    // Match removed files to added files by hash (greedy 1:1)
    let mut moved = Vec::new();
    for (src_rel, hash, size) in &removed_hashes {
        if let Some(targets) = added_by_hash.get_mut(hash) {
            if let Some(idx) = targets.iter().position(|(_, s)| s == size) {
                let (tgt_rel, _) = targets.remove(idx);
                moved.push(MovedEntry {
                    source_path: src_rel.clone(),
                    target_path: tgt_rel,
                    hash_hex: hash.clone(),
                    file_size: *size,
                });
            }
        }
    }

    moved
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    fn create_diff_dirs() -> (TempDir, PathBuf, PathBuf) {
        let tmp = TempDir::new().unwrap();
        let src = tmp.path().join("source");
        let tgt = tmp.path().join("target");
        fs::create_dir_all(&src).unwrap();
        fs::create_dir_all(&tgt).unwrap();

        // Same file
        fs::write(src.join("same.txt"), "unchanged content").unwrap();
        fs::write(tgt.join("same.txt"), "unchanged content").unwrap();

        // Modified file
        fs::write(src.join("modified.txt"), "original").unwrap();
        fs::write(tgt.join("modified.txt"), "changed").unwrap();

        // Removed file
        fs::write(src.join("removed.txt"), "will be removed").unwrap();

        // Added file
        fs::write(tgt.join("added.txt"), "new file").unwrap();

        (tmp, src, tgt)
    }

    #[test]
    fn test_diff_basic() {
        let (_tmp, src, tgt) = create_diff_dirs();

        let filter = WalkFilter {
            skip_hidden: false,
            glob_matcher: None,
            max_depth: None,
            follow_symlinks: false,
        };

        let src_files = crate::utils::walk_files_filtered(&src, &filter);
        let tgt_files = crate::utils::walk_files_filtered(&tgt, &filter);

        let src_map: HashMap<String, FileInfo> = src_files
            .into_iter()
            .map(|(rel, abs, size)| {
                (
                    rel,
                    FileInfo {
                        abs_path: abs,
                        size,
                    },
                )
            })
            .collect();
        let tgt_map: HashMap<String, FileInfo> = tgt_files
            .into_iter()
            .map(|(rel, abs, size)| {
                (
                    rel,
                    FileInfo {
                        abs_path: abs,
                        size,
                    },
                )
            })
            .collect();

        let result = compare_maps(&src_map, &tgt_map, Algorithm::Blake3, true, false, None);

        assert_eq!(result.added.len(), 1);
        assert_eq!(result.removed.len(), 1);
        assert_eq!(result.modified.len(), 1);
        assert_eq!(result.unchanged.len(), 1);
    }

    #[test]
    fn test_diff_move_detection() {
        let tmp = TempDir::new().unwrap();
        let src = tmp.path().join("source");
        let tgt = tmp.path().join("target");
        fs::create_dir_all(&src).unwrap();
        fs::create_dir_all(&tgt).unwrap();

        let content = vec![42u8; 1000];
        fs::write(src.join("old_name.bin"), &content).unwrap();
        fs::write(tgt.join("new_name.bin"), &content).unwrap();

        let filter = WalkFilter {
            skip_hidden: false,
            glob_matcher: None,
            max_depth: None,
            follow_symlinks: false,
        };

        let src_files = crate::utils::walk_files_filtered(&src, &filter);
        let tgt_files = crate::utils::walk_files_filtered(&tgt, &filter);

        let src_map: HashMap<String, FileInfo> = src_files
            .into_iter()
            .map(|(rel, abs, size)| {
                (
                    rel,
                    FileInfo {
                        abs_path: abs,
                        size,
                    },
                )
            })
            .collect();
        let tgt_map: HashMap<String, FileInfo> = tgt_files
            .into_iter()
            .map(|(rel, abs, size)| {
                (
                    rel,
                    FileInfo {
                        abs_path: abs,
                        size,
                    },
                )
            })
            .collect();

        let result = compare_maps(&src_map, &tgt_map, Algorithm::Blake3, true, true, None);

        assert_eq!(result.moved.len(), 1);
        assert_eq!(result.moved[0].source_path, "old_name.bin");
        assert_eq!(result.moved[0].target_path, "new_name.bin");
        assert_eq!(result.added.len(), 0);
        assert_eq!(result.removed.len(), 0);
    }
}
