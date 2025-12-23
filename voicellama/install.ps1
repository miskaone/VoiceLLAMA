#Requires -Version 5.1
<#
.SYNOPSIS
    VoiceLLAMA One-Click Installer for Windows
    Ultra-fast Text-to-Speech API Server powered by Kokoro-82M

.DESCRIPTION
    This script installs VoiceLLAMA and optionally configures Claude Code hooks.

.PARAMETER NoHooks
    Skip Claude Code hooks configuration

.PARAMETER NoVenv
    Install globally instead of in a virtual environment (not recommended)

.PARAMETER Dev
    Install development dependencies

.PARAMETER Start
    Start the server after installation

.EXAMPLE
    .\install.ps1
    Basic installation with hooks

.EXAMPLE
    .\install.ps1 -NoHooks -Start
    Install without hooks and start server
#>

[CmdletBinding()]
param(
    [switch]$NoHooks,
    [switch]$NoVenv,
    [switch]$Dev,
    [switch]$Start
)

# Configuration
$MinPythonVersion = [Version]"3.11"
$InstallDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $InstallDir "venv"

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Banner {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "                                                                " -ForegroundColor Cyan
    Write-Host "   VoiceLLAMA - Ultra-fast Text-to-Speech API Server            " -ForegroundColor Cyan
    Write-Host "   Powered by Kokoro-82M                                        " -ForegroundColor Cyan
    Write-Host "                                                                " -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info($message) {
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $message
}

function Write-Success($message) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $message
}

function Write-Warning($message) {
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $message
}

function Write-Error($message) {
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $message
}

function Test-Command($command) {
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

function Get-PythonCommand {
    # Try different Python commands
    $pythonCommands = @("python3.12", "python3.11", "python3", "python", "py -3.12", "py -3.11", "py -3")

    foreach ($cmd in $pythonCommands) {
        try {
            $cmdParts = $cmd -split " "
            $result = if ($cmdParts.Count -gt 1) {
                & $cmdParts[0] $cmdParts[1] -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            } else {
                & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            }

            if ($result) {
                $version = [Version]$result
                if ($version -ge $MinPythonVersion) {
                    return $cmd
                }
            }
        } catch {
            continue
        }
    }
    return $null
}

function Test-Python {
    Write-Info "Checking Python installation..."

    $script:PythonCmd = Get-PythonCommand

    if (-not $script:PythonCmd) {
        Write-Error "Python $MinPythonVersion or higher is required"
        Write-Host ""
        Write-Host "Please install Python 3.11+ from:"
        Write-Host "  - https://www.python.org/downloads/"
        Write-Host "  - Or use: winget install Python.Python.3.11"
        Write-Host ""
        Write-Host "Make sure to check 'Add Python to PATH' during installation"
        exit 1
    }

    $cmdParts = $script:PythonCmd -split " "
    $version = if ($cmdParts.Count -gt 1) {
        & $cmdParts[0] $cmdParts[1] --version 2>&1
    } else {
        & $script:PythonCmd --version 2>&1
    }
    Write-Success "Found $version"
}

function Test-Pip {
    Write-Info "Checking pip..."

    $cmdParts = $script:PythonCmd -split " "
    $result = if ($cmdParts.Count -gt 1) {
        & $cmdParts[0] $cmdParts[1] -m pip --version 2>&1
    } else {
        & $script:PythonCmd -m pip --version 2>&1
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Warning "pip not found, attempting to install..."
        $cmdParts = $script:PythonCmd -split " "
        if ($cmdParts.Count -gt 1) {
            & $cmdParts[0] $cmdParts[1] -m ensurepip --upgrade
        } else {
            & $script:PythonCmd -m ensurepip --upgrade
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install pip"
            exit 1
        }
    }

    Write-Success "pip is available"
}

function New-VirtualEnvironment {
    if ($NoVenv) {
        Write-Warning "Skipping virtual environment (-NoVenv)"
        return
    }

    Write-Info "Creating virtual environment..."

    if (Test-Path $VenvDir) {
        Write-Warning "Virtual environment already exists at $VenvDir"
        $response = Read-Host "Do you want to recreate it? [y/N]"
        if ($response -eq "y" -or $response -eq "Y") {
            Remove-Item -Recurse -Force $VenvDir
        } else {
            Write-Info "Using existing virtual environment"
            return
        }
    }

    $cmdParts = $script:PythonCmd -split " "
    if ($cmdParts.Count -gt 1) {
        & $cmdParts[0] $cmdParts[1] -m venv $VenvDir
    } else {
        & $script:PythonCmd -m venv $VenvDir
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }

    Write-Success "Virtual environment created at $VenvDir"
}

function Enable-VirtualEnvironment {
    if ($NoVenv) {
        return
    }

    Write-Info "Activating virtual environment..."

    $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"

    if (-not (Test-Path $activateScript)) {
        Write-Error "Virtual environment activation script not found"
        exit 1
    }

    & $activateScript
    Write-Success "Virtual environment activated"
}

function Install-Dependencies {
    Write-Info "Installing VoiceLLAMA..."

    Push-Location $InstallDir

    try {
        # Upgrade pip first
        pip install --upgrade pip

        # Install VoiceLLAMA with Kokoro
        if ($Dev) {
            pip install -e ".[dev,kokoro]"
            Write-Success "Installed VoiceLLAMA with dev dependencies"
        } else {
            pip install -e ".[kokoro]"
            Write-Success "Installed VoiceLLAMA"
        }
    } finally {
        Pop-Location
    }
}

function Test-FFmpeg {
    Write-Info "Checking for ffmpeg (optional, for MP3/OGG support)..."

    if (Test-Command "ffmpeg") {
        Write-Success "ffmpeg is installed"
    } else {
        Write-Warning "ffmpeg not found - MP3/OGG encoding will not be available"
        Write-Host "  To install ffmpeg:"
        Write-Host "    winget install ffmpeg"
        Write-Host "    Or download from: https://ffmpeg.org/download.html"
    }
}

function Set-ClaudeCodeHooks {
    if ($NoHooks) {
        Write-Info "Skipping Claude Code hooks configuration (-NoHooks)"
        return
    }

    Write-Info "Configuring Claude Code hooks..."

    $claudeDir = Join-Path $env:USERPROFILE ".claude"
    $settingsFile = Join-Path $claudeDir "settings.json"
    $hooksDir = Join-Path $InstallDir "src\voicellama\hooks"

    # Create .claude directory if it doesn't exist
    if (-not (Test-Path $claudeDir)) {
        New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
    }

    # Check if settings.json exists
    if (Test-Path $settingsFile) {
        Write-Warning "Claude Code settings already exist at $settingsFile"
        $response = Read-Host "Do you want to add VoiceLLAMA hooks to existing settings? [y/N]"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Info "Skipping hooks configuration"
            return
        }

        # Backup existing settings
        $backupFile = "$settingsFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $settingsFile $backupFile
        Write-Info "Backed up existing settings to $backupFile"
    }

    # Create or update settings using Python
    $pythonScript = @"
import json
import os
from pathlib import Path

settings_file = Path(r'$settingsFile')
hooks_dir = Path(r'$hooksDir')

# Default settings structure
default_settings = {
    "hooks": {}
}

# Load existing settings if they exist
if settings_file.exists():
    try:
        with open(settings_file, encoding='utf-8') as f:
            settings = json.load(f)
    except (json.JSONDecodeError, IOError):
        settings = default_settings.copy()
else:
    settings = default_settings.copy()

# Ensure hooks key exists
if "hooks" not in settings:
    settings["hooks"] = {}

# VoiceLLAMA hooks configuration
voicellama_hooks = {
    "PreToolUse": [
        {
            "matcher": "AskUserQuestion",
            "hooks": [
                {
                    "type": "command",
                    "command": f"python3 {hooks_dir}/tts_notify.py"
                }
            ]
        },
        {
            "matcher": ".*",
            "hooks": [
                {
                    "type": "command",
                    "command": f"python3 {hooks_dir}/tts_tool_notify.py"
                }
            ]
        }
    ],
    "PostToolUse": [
        {
            "matcher": ".*",
            "hooks": [
                {
                    "type": "command",
                    "command": f"python3 {hooks_dir}/context_tracker.py"
                }
            ]
        }
    ],
    "Stop": [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": f"python3 {hooks_dir}/tts_stop_notify.py"
                }
            ]
        }
    ]
}

# Merge hooks (add VoiceLLAMA hooks if not present)
for event, hooks_list in voicellama_hooks.items():
    if event not in settings["hooks"]:
        settings["hooks"][event] = []

    # Check if VoiceLLAMA hooks already exist
    existing_commands = [
        h.get("hooks", [{}])[0].get("command", "")
        for h in settings["hooks"][event]
    ]

    for hook in hooks_list:
        hook_cmd = hook.get("hooks", [{}])[0].get("command", "")
        if "voicellama" not in " ".join(existing_commands).lower():
            settings["hooks"][event].append(hook)

# Write settings
with open(settings_file, "w", encoding='utf-8') as f:
    json.dump(settings, f, indent=2)

print(f"Hooks configured in {settings_file}")
"@

    $pythonScript | python

    Write-Success "Claude Code hooks configured"
}

function New-StartScript {
    Write-Info "Creating start scripts..."

    # PowerShell start script
    $startPs1 = Join-Path $InstallDir "start-voicellama.ps1"

    if ($NoVenv) {
        $ps1Content = @'
# VoiceLLAMA Start Script
Write-Host "Starting VoiceLLAMA TTS Server..."
Write-Host "Web UI: http://localhost:8333"
Write-Host "Settings: http://localhost:8333/settings"
Write-Host "Press Ctrl+C to stop"
Write-Host ""
voicellama serve @args
'@
    } else {
        $ps1Content = @'
# VoiceLLAMA Start Script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$activateScript = Join-Path $scriptDir "venv\Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    & $activateScript
}

Write-Host "Starting VoiceLLAMA TTS Server..."
Write-Host "Web UI: http://localhost:8333"
Write-Host "Settings: http://localhost:8333/settings"
Write-Host "Press Ctrl+C to stop"
Write-Host ""
voicellama serve @args
'@
    }

    $ps1Content | Out-File -FilePath $startPs1 -Encoding UTF8
    Write-Success "Created: $startPs1"

    # Batch file for double-click
    $startBat = Join-Path $InstallDir "start-voicellama.bat"

    if ($NoVenv) {
        $batContent = @'
@echo off
echo Starting VoiceLLAMA TTS Server...
echo Web UI: http://localhost:8333
echo Settings: http://localhost:8333/settings
echo Press Ctrl+C to stop
echo.
voicellama serve %*
pause
'@
    } else {
        $batContent = @'
@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Starting VoiceLLAMA TTS Server...
echo Web UI: http://localhost:8333
echo Settings: http://localhost:8333/settings
echo Press Ctrl+C to stop
echo.
voicellama serve %*
pause
'@
    }

    $batContent | Out-File -FilePath $startBat -Encoding ASCII
    Write-Success "Created: $startBat"
}

function Write-Instructions {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "              Installation Complete!                            " -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Quick Start:" -ForegroundColor Cyan
    Write-Host "  Double-click: start-voicellama.bat"
    Write-Host "  PowerShell:   .\start-voicellama.ps1"
    Write-Host ""
    Write-Host "Or manually:" -ForegroundColor Cyan
    if (-not $NoVenv) {
        Write-Host "  .\venv\Scripts\Activate.ps1"
    }
    Write-Host "  voicellama serve"
    Write-Host ""
    Write-Host "Access the UI:" -ForegroundColor Cyan
    Write-Host "  Settings: http://localhost:8333"
    Write-Host "  Avatar:   http://localhost:8333/avatar"
    Write-Host ""
    Write-Host "API Documentation:" -ForegroundColor Cyan
    Write-Host "  Health:   http://localhost:8333/v1/health"
    Write-Host "  Voices:   http://localhost:8333/v1/voices"
    Write-Host "  TTS:      POST http://localhost:8333/v1/tts/announce"
    Write-Host ""
    if (-not $NoHooks) {
        Write-Host "Claude Code Hooks:" -ForegroundColor Cyan
        Write-Host "  Hooks have been configured in ~/.claude/settings.json"
        Write-Host "  Restart Claude Code for hooks to take effect"
        Write-Host ""
    }
    Write-Host "Note:" -ForegroundColor Yellow -NoNewline
    Write-Host " The Kokoro model will be downloaded on first use (~200MB)"
    Write-Host ""
}

# Main installation flow
function Main {
    Write-Banner

    Write-Info "Starting installation..."
    Write-Host ""

    Test-Python
    Test-Pip
    New-VirtualEnvironment
    Enable-VirtualEnvironment
    Install-Dependencies
    Test-FFmpeg
    Set-ClaudeCodeHooks
    New-StartScript

    Write-Instructions

    if ($Start) {
        Write-Info "Starting VoiceLLAMA server..."
        voicellama serve
    }
}

# Run main
Main
