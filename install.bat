@echo off
setlocal enabledelayedexpansion
title Uplinx Meta Manager - Installer
color 0A

echo.
echo  ============================================
echo   UPLINX META MANAGER - INSTALLER
echo  ============================================
echo.

REM ── Architecture detection (info only) ───────────────────────────────────
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    echo  System: 64-bit Windows detected
) else if "%PROCESSOR_ARCHITEW6432%"=="AMD64" (
    echo  System: 32-bit process on 64-bit Windows detected
) else (
    echo  System: 32-bit Windows detected
)
echo.

REM ── Python check ─────────────────────────────────────────────────────────
echo  Checking for Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed or not in PATH.
    echo.
    echo  Please download and install Python 3.11 from:
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation tick the box:
    echo    "Add Python to PATH"
    echo.
    echo  After installing Python, run install.bat again.
    echo.
    goto :error
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  Found: %PYVER%
echo.

REM ── Clean up old venv ─────────────────────────────────────────────────────
if exist venv (
    echo  Removing previous installation...
    rmdir /s /q venv 2>nul
    if exist venv (
        echo  WARNING: Could not remove old venv - it may be in use.
        echo  Please close any other terminals running the app and try again.
        goto :error
    )
    echo  Done.
)

REM ── Create virtual environment ────────────────────────────────────────────
echo.
echo  [1/5] Creating virtual environment...
python -m venv venv
if not exist venv\Scripts\python.exe (
    echo.
    echo  ERROR: Virtual environment creation failed.
    echo  Try: python -m pip install --upgrade pip
    echo.
    goto :error
)
echo         OK

REM ── Install dependencies ──────────────────────────────────────────────────
echo  [2/5] Installing packages (may take 3-5 minutes)...
echo         Please wait, do not close this window.
echo.
venv\Scripts\pip install --upgrade pip --quiet
venv\Scripts\pip install -r requirements.txt --no-warn-script-location
echo.
echo  [2/5] Packages installed.

REM ── Create .env file ──────────────────────────────────────────────────────
echo  [3/5] Setting up configuration file...
if not exist .env (
    copy .env.example .env >nul 2>&1

    REM Generate SECRET_KEY
    venv\Scripts\python -c "import secrets; f=open('.env','r'); t=f.read(); f.close(); t=t.replace('generate_64_char_random_string_here', secrets.token_hex(32)); f=open('.env','w'); f.write(t); f.close()"

    REM Generate ENCRYPTION_KEY
    venv\Scripts\python -c "from cryptography.fernet import Fernet; f=open('.env','r'); t=f.read(); f.close(); t=t.replace('generate_fernet_key_here', Fernet.generate_key().decode()); f=open('.env','w'); f.write(t); f.close()"

    echo         .env created with auto-generated security keys.
) else (
    echo         .env already exists - your settings are unchanged.
)

REM ── Create required folders ───────────────────────────────────────────────
echo  [4/5] Creating folders...
if not exist uploads         mkdir uploads
if not exist skills          mkdir skills
if not exist skills\global   mkdir skills\global
if not exist skills\clients  mkdir skills\clients
if not exist logs            mkdir logs
echo         OK

REM ── All done ──────────────────────────────────────────────────────────────
echo  [5/5] Done.
echo.
echo  ============================================
echo   INSTALLATION COMPLETE!
echo  ============================================
echo.
echo   Next steps:
echo.
echo   1. Open the file named  .env  in this folder
echo      (right-click > Open with > Notepad)
echo.
echo   2. Fill in these three values:
echo        META_APP_ID=
echo        META_APP_SECRET=
echo        ANTHROPIC_API_KEY=
echo.
echo   3. Save .env
echo.
echo   4. Double-click  start.bat  to launch the app
echo.
echo  ============================================
echo.
pause
endlocal
exit /b 0

:error
echo.
echo  Installation did not complete. See message above.
echo.
pause
endlocal
exit /b 1
