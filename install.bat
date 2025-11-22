@echo off
REM Kokoro Local TTS - Automated Installation Script for Windows
REM This script sets up the complete environment with all dependencies

echo.
echo ========================================
echo   Kokoro Local TTS - Setup Wizard
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% detected

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo.
    echo [*] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo.
echo [*] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Upgrade pip, setuptools, wheel
echo.
echo [*] Upgrading pip, setuptools, wheel...
python -m pip install --upgrade pip setuptools wheel -q
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip
    pause
    exit /b 1
)
echo [OK] pip/setuptools/wheel upgraded

REM Install PyTorch from official index (CPU)
echo.
echo [*] Installing PyTorch 2.1.2 (CPU)...
echo     This may take a few minutes...
python -m pip install torch==2.1.2 torchaudio==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu -q
if errorlevel 1 (
    echo [ERROR] Failed to install PyTorch
    pause
    exit /b 1
)
echo [OK] PyTorch installed successfully

REM Install all other requirements
echo.
echo [*] Installing all dependencies from requirements.txt...
echo     This may take several minutes...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo [ERROR] Failed to install requirements
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo [OK] All dependencies installed

REM Verify installation
echo.
echo [*] Verifying installation...
python -c "import torch; import kokoro; import transformers; print('[OK] All imports successful')"
if errorlevel 1 (
    echo [WARNING] Some imports failed
    echo Try running: python -m pip install --upgrade -r requirements.txt
    pause
    exit /b 1
)

REM Success
echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo [OK] Kokoro Local TTS is ready to use
echo.
echo To launch the application, run:
echo   python app.py
echo.
echo Or double-click: run_app.bat
echo.
pause
