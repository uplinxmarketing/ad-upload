@echo off
title Uplinx Meta Manager
echo ============================================
echo  Uplinx Meta Manager
echo ============================================
echo.

REM ── Check .env exists ────────────────────────────────────────────────────
if not exist .env (
    echo ERROR: .env file not found.
    echo.
    echo Please run install.bat first, then fill in your API keys.
    echo.
    pause
    exit /b 1
)

REM ── Check venv exists ─────────────────────────────────────────────────────
if not exist venv\Scripts\activate.bat (
    echo ERROR: Virtual environment not found.
    echo.
    echo Please run install.bat first.
    echo.
    pause
    exit /b 1
)

REM ── Warn if keys are still placeholders ──────────────────────────────────
findstr /c:"META_APP_ID=your_meta_app_id" .env >nul 2>&1
if not errorlevel 1 (
    echo WARNING: META_APP_ID is not set in .env
    echo.
    echo Please open the .env file and fill in your credentials before starting.
    echo.
    pause
    exit /b 1
)

findstr /c:"ANTHROPIC_API_KEY=your_anthropic_api_key" .env >nul 2>&1
if not errorlevel 1 (
    echo WARNING: ANTHROPIC_API_KEY is not set in .env
    echo.
    echo Please open the .env file and fill in your Anthropic API key.
    echo.
    pause
    exit /b 1
)

REM ── Activate venv ────────────────────────────────────────────────────────
call venv\Scripts\activate.bat

REM ── Open browser after 2 seconds ─────────────────────────────────────────
echo Starting server at http://localhost:8000
echo Press Ctrl+C to stop the server.
echo.
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

REM ── Start server ─────────────────────────────────────────────────────────
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start.
    echo Check the error above for details.
    echo Common fixes:
    echo   - Port 8000 in use: change --port 8000 above to --port 8001
    echo   - Missing package: run install.bat again
    echo.
    pause
)
