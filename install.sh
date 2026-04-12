#!/bin/bash

set -e

echo ""
echo "  HelloChusquis Installer"
echo "  ─────────────────────────"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python3 not found. Install it from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_VERSION" -lt 10 ]; then
    echo "  ✗ Python 3.10+ required. Current: 3.$PYTHON_VERSION"
    exit 1
fi

echo "  ✓ Python3 found"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "  ✗ pip3 not found."
    exit 1
fi

echo "  ✓ pip3 found"

# Install dir
INSTALL_DIR="$HOME/.hellochusquis-app"

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
    echo "  Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull origin main --quiet
else
    echo "  Cloning HelloChusquis..."
    git clone https://github.com/aminoy77/HelloChusquis.git "$INSTALL_DIR" --quiet
    cd "$INSTALL_DIR"
fi

# Install dependencies
echo "  Installing dependencies..."
pip3 install -e . --quiet --break-system-packages 2>/dev/null || pip3 install -e . --quiet

# Check PATH
PYTHON_BIN=$(python3 -c "import sysconfig; print(sysconfig.get_path('scripts'))")
if [[ ":$PATH:" != *":$PYTHON_BIN:"* ]]; then
    echo ""
    echo "  ⚠ Add this to your ~/.zshrc or ~/.bashrc:"
    echo "    export PATH=\"\$PATH:$PYTHON_BIN\""
    echo ""
    echo "  Then run: source ~/.zshrc"
else
    echo "  ✓ PATH configured"
fi

echo ""
echo "  ✓ HelloChusquis installed successfully!"
echo ""
echo "  Run: hellochusquis"
echo ""