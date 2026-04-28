@echo off
title Uplinx Meta Manager - Installer
echo ============================================
echo  Uplinx Meta Manager - Installer
echo ============================================
echo.

REM ── Check Python exists ──────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo.
    echo Please install Python 3.10 or newer from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo Then close this window and run install.bat again.
    echo.
    pause
    exit /b 1
)

REM Print Python version for info
echo Python found:
python --version
echo.

REM ── Create virtual environment ───────────────────────────────────────────
echo [1/7] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    echo Try running: python -m pip install virtualenv
    echo.
    pause
    exit /b 1
)
echo       Done.

REM ── Activate venv ────────────────────────────────────────────────────────
echo [2/7] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Could not activate virtual environment.
    pause
    exit /b 1
)
echo       Done.

REM ── Upgrade pip ──────────────────────────────────────────────────────────
echo [3/7] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: pip upgrade failed, continuing anyway...
)
echo.

REM ── Install dependencies ─────────────────────────────────────────────────
echo [4/7] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Dependency installation failed.
    echo Check your internet connection and try again.
    echo If the error mentions a specific package, note it down.
    echo.
    pause
    exit /b 1
)
echo       Done.

REM ── Set up .env ───────────────────────────────────────────────────────────
echo [5/7] Setting up configuration...
if not exist .env (
    copy .env.example .env >nul
    echo       Created .env from template.

    REM Generate keys using Python (after venv is active, cryptography is installed)
    python -c "import secrets, sys; sys.stdout.write(secrets.token_hex(32))" > _tmp_sk.txt 2>nul
    python -c "from cryptography.fernet import Fernet; import sys; sys.stdout.write(Fernet.generate_key().decode())" > _tmp_ek.txt 2>nul

    python -c "
sk = open('_tmp_sk.txt').read().strip()
ek = open('_tmp_ek.txt').read().strip()
txt = open('.env').read()
txt = txt.replace('generate_64_char_random_string_here', sk)
txt = txt.replace('generate_fernet_key_here', ek)
open('.env', 'w').write(txt)
print('      Security keys generated.')
"
    del _tmp_sk.txt _tmp_ek.txt >nul 2>&1
) else (
    echo       .env already exists, skipping.
)

REM ── Create directories ────────────────────────────────────────────────────
echo [6/7] Creating required directories...
if not exist uploads mkdir uploads
if not exist skills\global mkdir skills\global
if not exist skills\clients mkdir skills\clients
echo       Done.

REM ── Initialize database ───────────────────────────────────────────────────
echo [7/7] Initializing database...
python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
if errorlevel 1 (
    echo WARNING: Database init had an issue. It will be retried on first launch.
)
echo       Done.

echo.
echo ============================================
echo  INSTALLATION COMPLETE!
echo.
echo  NEXT STEPS:
echo  1. Open the .env file in this folder
echo  2. Fill in your API keys:
echo       META_APP_ID=
echo       META_APP_SECRET=
echo       ANTHROPIC_API_KEY=
echo  3. Save .env and double-click start.bat
echo ============================================
echo.
pause
