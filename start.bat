@echo off
setlocal enabledelayedexpansion
title Uplinx Meta Manager
color 0A

echo.
echo  ============================================
echo   UPLINX META MANAGER
echo  ============================================
echo.

REM ── Check venv exists ────────────────────────────────────────────────────
if not exist venv\Scripts\python.exe (
    echo  ERROR: App is not installed yet.
    echo.
    echo  Please run install.bat first.
    echo.
    pause
    exit /b 1
)

REM ── Check .env exists ────────────────────────────────────────────────────
if not exist .env (
    echo  ERROR: .env file not found.
    echo.
    echo  Please run install.bat first, then fill in your API keys.
    echo.
    pause
    exit /b 1
)

REM ── Check API keys are filled in ─────────────────────────────────────────
findstr /c:"META_APP_ID=your_meta_app_id" .env >nul 2>&1
if not errorlevel 1 (
    echo  WARNING: META_APP_ID is not set.
    echo.
    echo  Open .env in Notepad and fill in your Meta App credentials.
    echo  See README.md for instructions on getting your credentials.
    echo.
    pause
    exit /b 1
)

findstr /c:"ANTHROPIC_API_KEY=your_anthropic_api_key" .env >nul 2>&1
if not errorlevel 1 (
    echo  WARNING: ANTHROPIC_API_KEY is not set.
    echo.
    echo  Open .env in Notepad and add your Anthropic API key.
    echo  Get one at: https://console.anthropic.com/
    echo.
    pause
    exit /b 1
)

REM ── Launch ───────────────────────────────────────────────────────────────
echo  Starting server at http://localhost:8000
echo  Press Ctrl+C to stop.
echo.

REM Open browser after 3 seconds in background
start "" /b cmd /c "timeout /t 3 /nobreak >nul 2>&1 && start http://localhost:8000"

REM Start the server using venv python directly
venv\Scripts\uvicorn main:app --host 127.0.0.1 --port 8000 --reload

echo.
echo  Server stopped.
echo.
pause
endlocal
