@echo off
setlocal enabledelayedexpansion
title Uplinx Meta Manager - Installer
color 0A

echo.
echo  ============================================
echo   UPLINX META MANAGER - INSTALLER
echo  ============================================
echo.

REM ── Python check ─────────────────────────────────────────────────────────────
echo  Checking for Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed or not in PATH.
    echo.
    echo  Please download and install Python 3.11 or newer from:
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

REM ── Clean up old venv ─────────────────────────────────────────────────────────
if exist venv (
    echo  Removing previous installation...
    rmdir /s /q venv 2>nul
    echo  Done.
    echo.
)

REM ── Create virtual environment ────────────────────────────────────────────────
echo  [1/5] Creating virtual environment...

python -m venv venv 2>&1
if exist venv\Scripts\python.exe goto :venv_ok

REM venv failed — try with --without-pip fallback
echo  First attempt failed, trying alternate method...
python -m venv venv --without-pip 2>&1
if exist venv\Scripts\python.exe goto :venv_ok

echo.
echo  ERROR: Could not create a virtual environment.
echo.
echo  Common causes:
echo    1. Python installation is incomplete or corrupted
echo       Solution: Reinstall Python from python.org (tick "Add to PATH")
echo.
echo    2. This folder is on a network drive or has permission issues
echo       Solution: Move the folder to your Desktop or Documents
echo.
echo    3. Antivirus is blocking venv creation
echo       Solution: Temporarily disable antivirus, then reinstall
echo.
goto :error

:venv_ok
echo         OK

REM ── Install dependencies ──────────────────────────────────────────────────────
echo  [2/5] Installing packages (may take 3-5 minutes)...
echo         Please wait, do not close this window.
echo.

REM If venv was created without pip, bootstrap it first
if not exist venv\Scripts\pip.exe (
    echo  Bootstrapping pip...
    venv\Scripts\python -m ensurepip --upgrade
)

venv\Scripts\pip install -r requirements.txt --no-warn-script-location
echo.
echo  [2/5] Packages installed.

REM ── Create .env file ──────────────────────────────────────────────────────────
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

REM ── Create required folders ───────────────────────────────────────────────────
echo  [4/5] Creating folders...
if not exist uploads         mkdir uploads
if not exist skills          mkdir skills
if not exist skills\global   mkdir skills\global
if not exist skills\clients  mkdir skills\clients
if not exist logs            mkdir logs
echo         OK

REM ── All done ──────────────────────────────────────────────────────────────────
echo  [5/5] Done.
echo.
echo  ============================================
echo   INSTALLATION COMPLETE!
echo  ============================================
echo.
echo   Next steps:
echo.
echo   Double-click one of these to launch:
echo.
echo     start_tray.bat  — runs silently in the system tray
echo                       (no terminal window, recommended)
echo.
echo     start.bat       — runs with a terminal window
echo                       (use this to see logs / errors)
echo.
echo   The app opens automatically in your browser.
echo   A setup wizard will guide you through entering
echo   your API keys.
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
