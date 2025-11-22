@echo off
REM Kokoro Local TTS - Quick Launch Script
REM This script activates the virtual environment and launches the app

if not exist ".venv" (
    echo [ERROR] Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python app.py
pause
