@echo off
echo ============================================
echo  Uplinx Meta Manager - Windows Installer
echo ============================================

REM Check Python 3.10+
python --version 2>nul | findstr /r "3\.[1-9][0-9]\|3\.1[0-9]" >nul
if errorlevel 1 (
    echo ERROR: Python 3.10+ is required.
    echo Download from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/8] Creating virtual environment...
python -m venv venv

echo [2/8] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/8] Upgrading pip...
pip install --upgrade pip --quiet

echo [4/8] Installing dependencies...
pip install -r requirements.txt --quiet

echo [5/8] Setting up configuration...
if not exist .env (
    copy .env.example .env
    REM Generate SECRET_KEY using Python
    for /f "delims=" %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set SECRET_KEY=%%i
    REM Generate ENCRYPTION_KEY using Python
    for /f "delims=" %%i in ('python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"') do set ENCRYPTION_KEY=%%i
    REM Write keys to .env using Python
    python -c "
import re
with open('.env', 'r') as f:
    content = f.read()
content = content.replace('generate_64_char_random_string_here', r'%SECRET_KEY%')
content = content.replace('generate_fernet_key_here', r'%ENCRYPTION_KEY%')
with open('.env', 'w') as f:
    f.write(content)
"
    echo Generated security keys in .env
)

echo [6/8] Creating directories...
if not exist uploads mkdir uploads
if not exist skills\global mkdir skills\global
if not exist skills\clients mkdir skills\clients

echo [7/8] Initializing database...
python -c "import asyncio; from database import init_db; asyncio.run(init_db())"

echo [8/8] Setup complete!
echo.
echo ============================================
echo  NEXT STEPS:
echo  1. Edit .env with your API credentials
echo  2. Run start.bat to launch the app
echo ============================================
pause
