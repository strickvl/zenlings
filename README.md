# Zenlings 🎯

Interactive exercises for learning ZenML dynamic pipelines, inspired by [Rustlings](https://github.com/rust-lang/rustlings).

## What is Zenlings?

Zenlings teaches you ZenML's dynamic pipelines feature through hands-on exercises. Dynamic pipelines let you use Python control flow (loops, conditionals) to decide what steps to run at runtime—enabling powerful patterns like fan-out/fan-in, hyperparameter search, and conditional execution.

## Prerequisites

- **Python 3.9+**
- **ZenML installed**: `pip install zenml`
- **ZenML initialized**: Run `zenml init` in your project directory

## Installation

### From Source (Development)

```bash
cd zenlings
cargo build --release
./target/release/zenlings
```

### With Cargo

```bash
cargo install --path .
```

## Usage

```bash
# Start zenlings in the pack directory
cd zenlings
zenlings

# Or specify the path explicitly
zenlings --path /path/to/zenlings

# Jump to a specific exercise
zenlings --exercise load1

# Use simple verification (exit code only, no ZenML check)
zenlings --simple-verify
```

## Key Bindings

| Key | Action |
|-----|--------|
| `h` | Show hint for current exercise |
| `n` | Move to next exercise |
| `p` | Move to previous exercise |
| `l` | List all exercises |
| `r` | Re-run current exercise |
| `s` | Show solution |
| `q` | Quit |

## How It Works

1. **Watch Mode**: Zenlings watches your exercise files for changes
2. **Auto-Verification**: When you save a file, it automatically runs the exercise
3. **Status Check**: It verifies the ZenML pipeline completed successfully
4. **Progress Tracking**: Your progress is saved to `.zenlings-progress.json`

## Exercises

Exercises are organized into modules:

- **00_intro**: Introduction to dynamic pipelines
- **01_loading**: Loading artifacts with `.load()`
- **02_map**: The map pattern with `.map()`
- **03_product**: Cartesian products with `.product()`
- **04_advanced**: Advanced patterns (unmapped, chunk, unpack)
- **05_async**: Async execution with `.submit()`
- **06_config**: Runtime configuration
- **07_quizzes**: Capstone exercises

## Creating Exercises

Exercises are defined in `info.toml`:

```toml
[[exercises]]
name = "exercise_name"
dir = "00_intro"
pipeline_name = "my_pipeline"  # Optional, defaults to {name}_pipeline
hint = """
Your hint here...
"""
```

Exercise files go in `exercises/{dir}/{name}.py`.
Solutions go in `solutions/{dir}/{name}.py`.

## Development

```bash
# Build in debug mode
cargo build

# Build in release mode
cargo build --release

# Run tests
cargo test
```

## License

Apache-2.0
