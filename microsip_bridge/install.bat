@echo off
title MicroSIP Bridge Installer
color 0A
echo ============================================================
echo   MicroSIP ERPNext Bridge — One-Click Setup & Installer
echo ============================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to CHECK "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies (requests, pystray, pillow)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Failed to install optional tray packages. Continuing with core libraries...
    pip install requests
)

echo.
echo [2/3] Registering Windows Auto-Start (Silent Startup on Windows Boot)...

set SCRIPT_DIR=%~dp0
set VBS_STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MicroSIP_Bridge.vbs

:: Create a VBScript in Windows Startup folder to run pythonw.exe completely silently (no CMD window)
(
echo Set WshShell = CreateObject("WScript.Shell"^)"
echo WshShell.Run "pythonw """ ^& "%SCRIPT_DIR%microsip_bridge.pyw" ^& """", 0, False
) > "%VBS_STARTUP%"

if exist "%VBS_STARTUP%" (
    echo [SUCCESS] Windows Auto-Start registered in Startup folder.
    echo           The bridge will automatically run in background on Windows boot!
) else (
    echo [WARNING] Could not write to Startup folder. You can launch manually.
)

echo.
echo [3/3] Opening Graphical Settings Window...
echo.

:: Launch the script using pythonw (GUI mode)
start pythonw "%SCRIPT_DIR%microsip_bridge.pyw"

echo ============================================================
echo   Installation Complete!
echo   The Settings Window has opened. Please enter your ERPNext
echo   URL, API Key, and Secret, then click "Save & Run in Background".
echo ============================================================
timeout /t 5
