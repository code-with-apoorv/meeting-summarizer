@echo off
echo ===================================================
echo   MeetPulse AI - Meeting Summarizer Starting Up
echo ===================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

:: Create virtual environment if it does not exist
if not exist "venv" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo [2/3] Installing dependencies...
pip install -r backend\requirements.txt --quiet

:: Generate sample audio files if missing
echo [3/3] Generating sample test audio...
python backend\samples\generate_sample_audio.py

echo.
echo ===================================================
echo   Server is running at: http://localhost:8000
echo   API Docs available at: http://localhost:8000/docs
echo ===================================================
echo.

:: Start FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
