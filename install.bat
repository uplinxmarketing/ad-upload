@echo off
title Uplinx Meta Manager - Installer
echo ============================================
echo  Uplinx Meta Manager - Installer
echo ============================================
echo.
echo All output is also saved to: install_log.txt
echo.

REM Start logging everything to a file
set LOGFILE=install_log.txt
echo Install started: %date% %time% > %LOGFILE%

REM ── Check Python exists ──────────────────────────────────────────────────
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo ERROR: Python not found >> %LOGFILE%
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
python --version
python --version >> %LOGFILE% 2>&1
echo.

REM ── Remove old venv for a clean install ─────────────────────────────────
if exist venv (
    echo Removing old virtual environment for clean install...
    rmdir /s /q venv
    echo       Old venv removed.
)

REM ── Create virtual environment ───────────────────────────────────────────
echo [1/7] Creating virtual environment...
python -m venv venv >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    echo ERROR: venv creation failed >> %LOGFILE%
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
    echo ERROR: venv activate failed >> %LOGFILE%
    echo.
    pause
    exit /b 1
)
echo       Done.

REM ── Upgrade pip ──────────────────────────────────────────────────────────
echo [3/7] Upgrading pip...
python -m pip install --upgrade pip >> %LOGFILE% 2>&1
echo       Done.

REM ── Install dependencies ─────────────────────────────────────────────────
echo [4/7] Installing dependencies (this may take a few minutes)...
echo.
pip install -r requirements.txt
echo.

REM Do not check errorlevel here - pip returns 1 on Windows even on success
REM (pywin32 post-install scripts trigger this false positive)
REM Instead verify by actually importing key packages:
echo       Verifying installation...
python -c "import fastapi, anthropic, sqlalchemy, cryptography, fastmcp" 2>&1
if errorlevel 1 (
    echo.
    echo ============================================
    echo  ERROR: Some packages failed to import.
    echo ============================================
    echo.
    echo Try running install.bat as Administrator:
    echo   Right-click install.bat ^> Run as administrator
    echo.
    pause
    exit /b 1
)
echo [4/7] Done.

REM ── Set up .env ───────────────────────────────────────────────────────────
echo [5/7] Setting up configuration...
if not exist .env (
    copy .env.example .env >nul
    echo       Created .env from template.

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
" >> %LOGFILE% 2>&1
    echo       Security keys generated.
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
python -c "import asyncio; from database import init_db; asyncio.run(init_db())" >> %LOGFILE% 2>&1
if errorlevel 1 (
    echo       WARNING: DB init issue - will retry on first launch.
) else (
    echo       Done.
)

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
