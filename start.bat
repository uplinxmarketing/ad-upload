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
    echo  Please run install.bat first.
    echo.
    pause
    exit /b 1
)

REM ── Launch ───────────────────────────────────────────────────────────────
echo  Starting server at http://localhost:8000
echo  Press Ctrl+C to stop.
echo.
echo  The app will open in your browser automatically.
echo  If it does not open, visit: http://localhost:8000
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
