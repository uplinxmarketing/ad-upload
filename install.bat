@echo off
setlocal enabledelayedexpansion
title Uplinx Meta Manager - Installer
color 0A

REM ── Always run from the folder that contains install.bat ─────────────────────
cd /d "%~dp0"

echo.
echo  ============================================
echo   UPLINX META MANAGER - INSTALLER
echo  ============================================
echo.

REM ── Find a working Python (avoid Windows Store stub) ─────────────────────────
echo  Checking for Python...

REM Prefer the 'py' launcher (bypasses Windows Store stub)
set PYTHON=
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=py
) else (
    REM Fall back to python, but skip the Windows Store stub at System32
    for /f "tokens=*" %%F in ('where python 2^>nul') do (
        if "!PYTHON!"=="" (
            echo %%F | findstr /i "WindowsApps\WindowsStore\System32" >nul 2>&1
            if errorlevel 1 (
                set PYTHON=%%F
            )
        )
    )
)

if "!PYTHON!"=="" (
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

for /f "tokens=*" %%i in ('!PYTHON! --version 2^>^&1') do set PYVER=%%i
echo  Found: %PYVER%  (using: !PYTHON!)
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

REM Use full absolute path for the venv to avoid Store-stub working-dir bugs
!PYTHON! -m venv "%~dp0venv" 2>&1
if exist "%~dp0venv\Scripts\python.exe" goto :venv_ok

REM Retry with --without-pip
echo  First attempt failed, trying without pip...
!PYTHON! -m venv "%~dp0venv" --without-pip 2>&1
if exist "%~dp0venv\Scripts\python.exe" goto :venv_ok

echo.
echo  ERROR: Could not create a virtual environment.
echo.
echo  Most common fix:
echo    Move this folder out of Downloads to your Desktop,
echo    then run install.bat again.
echo.
echo  Other causes:
echo    - Antivirus blocking venv creation (temporarily disable it)
echo    - Corrupted Python (reinstall from python.org)
echo.
goto :error

:venv_ok
echo         OK

REM ── Install dependencies ──────────────────────────────────────────────────────
echo  [2/5] Installing packages (may take 3-5 minutes)...
echo         Please wait, do not close this window.
echo.

if not exist "%~dp0venv\Scripts\pip.exe" (
    echo  Bootstrapping pip...
    "%~dp0venv\Scripts\python.exe" -m ensurepip --upgrade
)

"%~dp0venv\Scripts\pip.exe" install -r "%~dp0requirements.txt" --no-warn-script-location
echo.
echo  [2/5] Packages installed.

REM ── Create .env file ──────────────────────────────────────────────────────────
echo  [3/5] Setting up configuration file...
if not exist "%~dp0.env" (
    copy "%~dp0.env.example" "%~dp0.env" >nul 2>&1

    "%~dp0venv\Scripts\python.exe" -c "import secrets; f=open('.env','r'); t=f.read(); f.close(); t=t.replace('generate_64_char_random_string_here', secrets.token_hex(32)); f=open('.env','w'); f.write(t); f.close()"
    "%~dp0venv\Scripts\python.exe" -c "from cryptography.fernet import Fernet; f=open('.env','r'); t=f.read(); f.close(); t=t.replace('generate_fernet_key_here', Fernet.generate_key().decode()); f=open('.env','w'); f.write(t); f.close()"

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
echo   Double-click one of these to launch:
echo.
echo     start_tray.bat  - runs silently in the system tray
echo                       (no terminal window, recommended)
echo.
echo     start.bat       - runs with a terminal window
echo                       (use if you see errors)
echo.
echo   The app will open in your browser automatically.
echo   A setup wizard lets you enter your API keys.
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
