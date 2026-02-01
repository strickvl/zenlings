#!/bin/sh
# Zenlings installer script
# Usage: curl -sSf https://raw.githubusercontent.com/strickvl/zenlings/main/install.sh | sh
#
# Environment variables:
#   ZENLINGS_VERSION    - Version to install (e.g., "v0.1.0"). Default: latest
#   ZENLINGS_INSTALL_DIR - Installation directory. Default: ~/.local/bin
#   ZENLINGS_REPO       - GitHub repository. Default: strickvl/zenlings

set -eu

# Configuration (can be overridden by environment variables)
ZENLINGS_REPO="${ZENLINGS_REPO:-strickvl/zenlings}"
ZENLINGS_INSTALL_DIR="${ZENLINGS_INSTALL_DIR:-$HOME/.local/bin}"

# Colors for output (disabled if not a terminal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Print functions
info() {
    printf "${BLUE}info:${NC} %s\n" "$1"
}

success() {
    printf "${GREEN}success:${NC} %s\n" "$1"
}

warn() {
    printf "${YELLOW}warning:${NC} %s\n" "$1" >&2
}

fatal() {
    printf "${RED}error:${NC} %s\n" "$1" >&2
    exit 1
}

# Check if a command exists
need_cmd() {
    if ! command -v "$1" > /dev/null 2>&1; then
        fatal "Required command '$1' not found. Please install it and try again."
    fi
}

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux" ;;
        Darwin*) echo "darwin" ;;
        CYGWIN*|MINGW*|MSYS*)
            fatal "Windows detected. Please download zenlings directly from:
    https://github.com/${ZENLINGS_REPO}/releases/latest

Download: zenlings-x86_64-pc-windows-msvc.exe"
            ;;
        *)
            fatal "Unsupported operating system: $(uname -s)
Zenlings supports: macOS (Intel/Apple Silicon) and Linux (x86_64)"
            ;;
    esac
}

# Detect CPU architecture
detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64)    echo "x86_64" ;;
        arm64|aarch64)   echo "aarch64" ;;
        *)
            fatal "Unsupported architecture: $(uname -m)
Zenlings supports: x86_64 (Intel/AMD) and aarch64 (Apple Silicon/ARM)"
            ;;
    esac
}

# Map OS and architecture to Rust target triple
compute_target() {
    os="$1"
    arch="$2"

    case "${os}-${arch}" in
        darwin-x86_64)   echo "x86_64-apple-darwin" ;;
        darwin-aarch64)  echo "aarch64-apple-darwin" ;;
        linux-x86_64)    echo "x86_64-unknown-linux-gnu" ;;
        linux-aarch64)
            fatal "Linux ARM64 is not currently supported.
Please build from source: cargo install zenlings"
            ;;
        *)
            fatal "Unsupported platform: ${os}-${arch}"
            ;;
    esac
}

# Get the asset filename for a target
asset_name() {
    target="$1"
    echo "zenlings-${target}"
}

# Download a file using curl or wget
download() {
    url="$1"
    output="$2"

    if command -v curl > /dev/null 2>&1; then
        curl -sSfL "$url" -o "$output"
    elif command -v wget > /dev/null 2>&1; then
        wget -q "$url" -O "$output"
    else
        fatal "Neither curl nor wget found. Please install one of them."
    fi
}

# Main installation function
install_zenlings() {
    info "Detecting platform..."

    os=$(detect_os)
    arch=$(detect_arch)
    target=$(compute_target "$os" "$arch")
    asset=$(asset_name "$target")

    info "Platform: ${os}/${arch} (${target})"

    # Determine download URL
    if [ -n "${ZENLINGS_VERSION:-}" ]; then
        url="https://github.com/${ZENLINGS_REPO}/releases/download/${ZENLINGS_VERSION}/${asset}"
        info "Downloading zenlings ${ZENLINGS_VERSION}..."
    else
        url="https://github.com/${ZENLINGS_REPO}/releases/latest/download/${asset}"
        info "Downloading latest zenlings..."
    fi

    # Create temp directory for download
    tmp_dir=$(mktemp -d)
    trap 'rm -rf "$tmp_dir"' EXIT

    tmp_file="${tmp_dir}/${asset}"

    # Download the binary
    info "Fetching from: ${url}"
    if ! download "$url" "$tmp_file"; then
        fatal "Failed to download zenlings. Please check:
  - Your internet connection
  - The version exists: https://github.com/${ZENLINGS_REPO}/releases
  - The release includes binaries for your platform (${target})"
    fi

    # Make executable
    chmod +x "$tmp_file"

    # Create install directory if needed
    if [ ! -d "$ZENLINGS_INSTALL_DIR" ]; then
        info "Creating directory: ${ZENLINGS_INSTALL_DIR}"
        mkdir -p "$ZENLINGS_INSTALL_DIR"
    fi

    # Install the binary
    install_path="${ZENLINGS_INSTALL_DIR}/zenlings"
    info "Installing to: ${install_path}"
    mv "$tmp_file" "$install_path"

    success "zenlings installed successfully!"

    # Check if install directory is in PATH
    case ":${PATH}:" in
        *":${ZENLINGS_INSTALL_DIR}:"*)
            # Already in PATH
            echo ""
            info "Run 'zenlings' to get started!"
            ;;
        *)
            echo ""
            warn "${ZENLINGS_INSTALL_DIR} is not in your PATH."
            echo ""
            echo "Add it to your shell configuration:"
            echo ""
            echo "  For bash (~/.bashrc):"
            echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            echo ""
            echo "  For zsh (~/.zshrc):"
            echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            echo ""
            echo "  For fish (~/.config/fish/config.fish):"
            echo "    set -gx PATH \$HOME/.local/bin \$PATH"
            echo ""
            echo "Then restart your shell or run:"
            echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
            echo ""
            ;;
    esac

    # Remind about Python requirements
    echo ""
    info "Next steps:"
    echo "  1. Ensure Python 3.9+ is installed"
    echo "  2. Install ZenML: pip install zenml"
    echo "  3. Initialize ZenML: zenml init && zenml login"
    echo "  4. Clone exercises: git clone https://github.com/${ZENLINGS_REPO}.git"
    echo "  5. cd zenlings && zenlings"
    echo ""
}

# Run the installer
install_zenlings
