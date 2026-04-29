@echo off
title Uplinx Meta Manager - Installer
echo ============================================
echo  Uplinx Meta Manager - Installer
echo ============================================
echo.

REM ── Check Python exists ──────────────────────────────────────────────────
echo Checking Python...
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
python --version
echo.

REM ── Remove old venv for a clean install ──────────────────────────────────
if exist venv (
    echo Removing old virtual environment for a clean install...
    rmdir /s /q venv
    echo       Old venv removed.
    echo.
)

REM ── Create virtual environment ───────────────────────────────────────────
echo [1/6] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo.
    echo ERROR: Failed to create virtual environment.
    echo.
    pause
    exit /b 1
)
echo       Done.

REM ── Activate venv ────────────────────────────────────────────────────────
echo [2/6] Activating virtual environment...
call venv\Scripts\activate.bat
echo       Done.

REM ── Upgrade pip ──────────────────────────────────────────────────────────
echo [3/6] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo       Done.

REM ── Install dependencies ─────────────────────────────────────────────────
echo [4/6] Installing dependencies (this may take a few minutes)...
echo.
pip install -r requirements.txt
echo.
echo [4/6] Done.

REM ── Set up .env ───────────────────────────────────────────────────────────
echo [5/6] Setting up configuration...
if not exist .env (
    copy .env.example .env >nul
    echo       Created .env from template.

    python -c "import secrets; open('_tmp_sk.txt','w').write(secrets.token_hex(32))"
    python -c "from cryptography.fernet import Fernet; open('_tmp_ek.txt','w').write(Fernet.generate_key().decode())"
    python -c "
sk=open('_tmp_sk.txt').read().strip()
ek=open('_tmp_ek.txt').read().strip()
txt=open('.env').read()
txt=txt.replace('generate_64_char_random_string_here',sk)
txt=txt.replace('generate_fernet_key_here',ek)
open('.env','w').write(txt)
"
    del _tmp_sk.txt _tmp_ek.txt >nul 2>&1
    echo       Security keys generated automatically.
) else (
    echo       .env already exists - keeping your existing settings.
)

REM ── Create directories + init DB ─────────────────────────────────────────
echo [6/6] Creating folders and initializing database...
if not exist uploads mkdir uploads
if not exist skills\global mkdir skills\global
if not exist skills\clients mkdir skills\clients
python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
echo       Done.

echo.
echo ============================================
echo  INSTALLATION COMPLETE!
echo.
echo  NEXT STEPS:
echo  1. Open the .env file in this folder
echo  2. Fill in your API keys:
echo       META_APP_ID=your_app_id
echo       META_APP_SECRET=your_app_secret
echo       ANTHROPIC_API_KEY=your_key
echo  3. Save .env then double-click start.bat
echo ============================================
echo.
pause
