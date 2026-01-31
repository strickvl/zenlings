# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zenlings is a Rustlings-inspired interactive CLI for learning ZenML's dynamic pipelines feature. It teaches hands-on through guided exercises with automatic verification.

**Architecture:** Rust CLI (file watching, TUI, verification orchestration) + Python exercises (ZenML pipelines).

## Common Commands

### Rust CLI

```bash
cargo build --release           # Build optimized binary
cargo install --path .          # Install as system binary
./target/release/zenlings       # Run from repo root
```

### Python Environment

```bash
uv venv && uv pip install -e ".[test]"  # Install with test dependencies
zenml init                               # Required before running exercises
```

### Running Tests

```bash
pytest tests/ -n auto --dist loadfile -v  # Parallel execution (recommended)
pytest tests/ -k "test_solution[intro1]"  # Single exercise test
```

### CLI Options

```bash
zenlings --exercise load1       # Jump to specific exercise
zenlings --simple-verify        # Exit code only (skip ZenML status check)
zenlings --no-watch             # Disable file watching
```

## Architecture

```
src/
├── main.rs        # CLI args, event loop, mpsc channels between watcher/verifier/TUI
├── app_state.rs   # Progress tracking (.zenlings-progress.json), exercise navigation
├── exercise.rs    # Parse info.toml, locate exercise files
├── verify.rs      # Run Python subprocess, parse ZenML pipeline status
├── watch.rs       # File watcher with debouncing (notify crate)
├── term.rs        # Terminal UI (crossterm), raw mode key handling
└── hints.rs       # Hint display logic
```

**Key flow:** File change → `watch.rs` debouncer → `verify.rs` subprocess → status parsed → `term.rs` renders result

### Startup Checks

On launch, Zenlings runs environment validation with animated progress display:
1. Python version ≥3.9
2. ZenML installed (Python package + CLI)
3. ZenML initialized (.zen directory)
4. Orchestrator type (warns if not 'local')

Skip with `--skip-checks`. The implementation uses background threads + spinner animation in `main.rs:run_startup_checks()`.

### Exercise Structure

- `exercises/{module}/{name}.py` - Student files with TODO comments
- `solutions/{module}/{name}.py` - Reference implementations
- `info.toml` - Exercise catalog (name, dir, pipeline_name, hints)

### Testing Isolation

Tests use pytest-xdist with per-worker HOME and .zen directories to avoid SQLite conflicts. Each worker runs `zenml init` in isolation.

## Key Files

- `info.toml` - Central exercise definitions (26 exercises across 8 modules)
- `.zenlings-progress.json` - User progress state (auto-created)
- `pyproject.toml` - Python deps (zenml[local], pytest, pytest-xdist)
- `Cargo.toml` - Rust deps (clap, crossterm, notify, serde, anyhow)

## Exercise Modules

00_intro → 01_loading → 02_map → 03_product → 04_advanced → 05_async → 06_config → 07_quizzes

Teaching progression: `.load()` → `.map()` → `.product()` → unmapped/chunk/unpack → `.submit()` → runtime config
