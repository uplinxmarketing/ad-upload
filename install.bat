@echo off
REM Launch the Uplinx GUI installer (PowerShell)
REM -Sta is required for Windows Forms (Single-Threaded Apartment)
powershell.exe -NoProfile -ExecutionPolicy Bypass -Sta -File "%~dp0installer.ps1"
