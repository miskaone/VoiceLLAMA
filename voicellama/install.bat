@echo off
REM VoiceLLAMA One-Click Installer for Windows
REM Double-click this file to install VoiceLLAMA
REM
REM This script launches the PowerShell installer
REM For more options, run: powershell -ExecutionPolicy Bypass -File install.ps1 -Help

echo.
echo ================================================================
echo   VoiceLLAMA - One-Click Installer
echo   Ultra-fast Text-to-Speech API Server
echo ================================================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: PowerShell is required but not found
    echo Please install PowerShell or run install.ps1 manually
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Run PowerShell installer with execution policy bypass
echo Starting PowerShell installer...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"

REM Check if installation succeeded
if %ERRORLEVEL% neq 0 (
    echo.
    echo Installation failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo.
echo To start VoiceLLAMA, double-click: start-voicellama.bat
echo.
pause
