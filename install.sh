#!/bin/bash
# Kokoro Local TTS - Automated Installation Script for Linux/macOS
# This script sets up the complete environment with all dependencies

set -e  # Exit on error

echo ""
echo "========================================"
echo "  Kokoro Local TTS - Setup Wizard"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.10+ using:"
    echo "  macOS: brew install python@3.10"
    echo "  Linux: sudo apt-get install python3.10"
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "[OK] Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "[*] Creating virtual environment..."
    python3 -m venv .venv
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "[*] Activating virtual environment..."
source .venv/bin/activate
echo "[OK] Virtual environment activated"

# Upgrade pip, setuptools, wheel
echo ""
echo "[*] Upgrading pip, setuptools, wheel..."
python -m pip install --upgrade pip setuptools wheel -q
echo "[OK] pip/setuptools/wheel upgraded"

# Install PyTorch from official index (CPU)
echo ""
echo "[*] Installing PyTorch 2.1.2 (CPU)..."
echo "    This may take a few minutes..."
python -m pip install torch==2.1.2 torchaudio==2.1.2 torchvision==0.16.2 -q
echo "[OK] PyTorch installed successfully"

# Install all other requirements
echo ""
echo "[*] Installing all dependencies from requirements.txt..."
echo "    This may take several minutes..."
python -m pip install -r requirements.txt -q
echo "[OK] All dependencies installed"

# Verify installation
echo ""
echo "[*] Verifying installation..."
python -c "import torch; import kokoro; import transformers; print('[OK] All imports successful')"

# Success
echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "[OK] Kokoro Local TTS is ready to use"
echo ""
echo "To launch the application, run:"
echo "  source .venv/bin/activate"
echo "  python app.py"
echo ""
