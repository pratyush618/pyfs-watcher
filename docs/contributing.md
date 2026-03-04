# Contributing

Thanks for your interest in contributing to pyfs-watcher!

## Prerequisites

- **Python 3.9+**
- **Rust 1.77+** (install via [rustup](https://rustup.rs))
- **maturin** — Python/Rust build tool

## Dev Setup

```bash
# Clone the repository
git clone https://github.com/pratyush618/pyfs-watcher.git
cd pyfs-watcher

# Create a virtual environment
uv venv && source .venv/bin/activate
# or: python -m venv .venv && source .venv/bin/activate

# Install dev dependencies
uv pip install -e ".[dev]"
# or: pip install -e ".[dev]"

# Build the Rust extension
maturin develop

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Rust tests
cargo test

# Python tests
pytest tests/

# Run a specific test
pytest tests/test_hash.py -v
```

## Code Quality

### Python

```bash
# Lint
ruff check py_src/ tests/ benches/

# Format
ruff format py_src/ tests/ benches/

# Type check
mypy py_src/
```

### Rust

```bash
# Format
cargo fmt --check

# Lint
cargo clippy -- -D warnings
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. To run them manually:

```bash
pre-commit run --all-files
```

---

## Adding a New Feature

Checklist for adding a new module (e.g., `compress`):

1. **Rust implementation** — Create `src/compress.rs` with the core logic
2. **PyO3 bindings** — Add `#[pyfunction]` and `#[pyclass]` items, register in `src/lib.rs`
3. **Type stubs** — Add signatures to `py_src/pyfs_watcher/_core.pyi`
4. **Python re-exports** — Add functions to `py_src/pyfs_watcher/__init__.py`, data classes to `types.py`, and errors to `errors.py`
5. **Error type** — Add a `CompressError` variant to `errors.rs` and the `.pyi` stub
6. **Tests** — Add `tests/test_compress.py`
7. **Documentation** — Add guide page and API reference page
8. **README** — Add usage example

---

## Building Docs Locally

```bash
# Install Zensical
pip install zensical
# or: uv pip install zensical

# Serve with live reload
zensical serve

# Build static site
zensical build --clean
```

Open `http://localhost:8000` to preview.

---

## Pull Requests

- Create a feature branch from `master`
- Make sure all tests pass (`cargo test && pytest tests/`)
- Make sure linters pass (`ruff check`, `cargo fmt --check`, `cargo clippy`)
- Write a clear PR description explaining what and why
