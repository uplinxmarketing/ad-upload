@echo off
echo Starting Uplinx Meta Manager...

REM Check .env exists
if not exist .env (
    echo ERROR: .env file not found. Run install.bat first.
    pause
    exit /b 1
)

REM Check META_APP_ID is configured
findstr /c:"META_APP_ID=your_meta_app_id" .env >nul
if not errorlevel 1 (
    echo WARNING: META_APP_ID not configured in .env
    echo Please edit .env with your credentials.
    pause
    exit /b 1
)

REM Activate venv
call venv\Scripts\activate.bat

echo Launching server at http://localhost:8000
start "" "http://localhost:8000"
timeout /t 2 /nobreak >nul

uvicorn main:app --host 127.0.0.1 --port 8000 --reload
