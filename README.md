# 🎯 Zenlings

**Learn ZenML's dynamic pipelines through hands-on exercises.**

Inspired by [rustlings](https://github.com/rust-lang/rustlings), Zenlings guides you through ZenML's powerful dynamic pipeline features — `.load()`, `.map()`, `.product()`, async execution, and more — with exercises that build on each other.

## Quick Start

### Install Zenlings

**macOS / Linux:**
```bash
curl -sSf https://raw.githubusercontent.com/strickvl/zenlings/main/install.sh | sh
```

**Windows:** Download [zenlings-x86_64-pc-windows-msvc.exe](https://github.com/strickvl/zenlings/releases/latest) from releases.

**From source** (requires Rust):
```bash
cargo install zenlings
```

### Get Started

```bash
# Clone the exercises
git clone https://github.com/strickvl/zenlings.git
cd zenlings

# Set up Python environment
uv venv && source .venv/bin/activate
uv pip install -e .

# Initialize ZenML
zenml init
zenml login

# Start learning!
zenlings
```

## Prerequisites

- Python 3.9+
- A ZenML account (free at [cloud.zenml.io](https://cloud.zenml.io))

## How It Works

Each exercise is a Python file with a `TODO` comment marking where you need to write code. Edit the file, press `r` to run, and Zenlings verifies your solution by checking that the pipeline completes successfully.

```
exercises/
├── 00_intro/       # Hello world pipelines
├── 01_loading/     # .load() - loading data
├── 02_map/         # .map() - parallel processing
├── 03_product/     # .product() - combining data
├── 04_advanced/    # Unmapped, chunk, unpack
├── 05_async/       # .submit() - async execution
├── 06_config/      # Runtime configuration
└── 07_quizzes/     # Put it all together
```

## Controls

| Key | Action |
|-----|--------|
| `r` | Run current exercise |
| `n` | Next exercise |
| `p` | Previous exercise |
| `h` | Show hint |
| `s` | Show solution |
| `o` | Open in editor |
| `l` | List all exercises |
| `q` | Quit |

## Tips

- **Read the comments** — each exercise explains what you need to do
- **Use hints sparingly** — try to figure it out first
- **Check the solution** if stuck — learning from examples is valid!

## Resources

- [ZenML Documentation](https://docs.zenml.io)
- [Dynamic Pipelines Guide](https://docs.zenml.io/how-to/pipeline-development/build-pipelines/dynamically-assign-artifact-names)

## License

MIT
