#!/bin/bash
#
# VoiceLLAMA One-Click Installer
# Ultra-fast Text-to-Speech API Server powered by Kokoro-82M
#
# Usage: ./install.sh [OPTIONS]
# Options:
#   --no-hooks      Skip Claude Code hooks configuration
#   --no-venv       Install globally (not recommended)
#   --dev           Install development dependencies
#   --start         Start server after installation
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MIN_PYTHON_VERSION="3.11"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${INSTALL_DIR}/venv"

# Parse arguments
INSTALL_HOOKS=true
USE_VENV=true
INSTALL_DEV=false
START_SERVER=false

for arg in "$@"; do
    case $arg in
        --no-hooks)
            INSTALL_HOOKS=false
            shift
            ;;
        --no-venv)
            USE_VENV=false
            shift
            ;;
        --dev)
            INSTALL_DEV=true
            shift
            ;;
        --start)
            START_SERVER=true
            shift
            ;;
        --help|-h)
            echo "VoiceLLAMA Installer"
            echo ""
            echo "Usage: ./install.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-hooks    Skip Claude Code hooks configuration"
            echo "  --no-venv     Install globally (not recommended)"
            echo "  --dev         Install development dependencies"
            echo "  --start       Start server after installation"
            echo "  --help, -h    Show this help message"
            exit 0
            ;;
    esac
done

# Helper functions
print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║   ╦  ╦┌─┐┬┌─┐┌─┐╦  ╦  ╔═╗╔╦╗╔═╗                             ║"
    echo "║   ╚╗╔╝│ ││││  ├┤ ║  ║  ╠═╣║║║╠═╣                             ║"
    echo "║    ╚╝ └─┘┴└─┘└─┘╩═╝╩═╝╩ ╩╩ ╩╩ ╩                             ║"
    echo "║                                                              ║"
    echo "║   Ultra-fast Text-to-Speech API Server                       ║"
    echo "║   Powered by Kokoro-82M                                      ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

version_gte() {
    # Compare version strings: returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check Python version
check_python() {
    log_info "Checking Python installation..."

    PYTHON_CMD=""

    # Try python3.12 first, then python3.11, then python3, then python
    for cmd in python3.12 python3.11 python3 python; do
        if check_command "$cmd"; then
            version=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            if version_gte "$version" "$MIN_PYTHON_VERSION"; then
                PYTHON_CMD="$cmd"
                break
            fi
        fi
    done

    if [ -z "$PYTHON_CMD" ]; then
        log_error "Python $MIN_PYTHON_VERSION or higher is required"
        echo ""
        echo "Please install Python 3.11+ from:"
        echo "  - https://www.python.org/downloads/"
        echo "  - Or use your package manager:"
        echo "    Ubuntu/Debian: sudo apt install python3.11"
        echo "    macOS: brew install python@3.11"
        echo "    Arch: sudo pacman -S python"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version)
    log_success "Found $PYTHON_VERSION"
    export PYTHON_CMD
}

# Check pip
check_pip() {
    log_info "Checking pip..."

    if ! $PYTHON_CMD -m pip --version &> /dev/null; then
        log_warning "pip not found, attempting to install..."
        $PYTHON_CMD -m ensurepip --upgrade || {
            log_error "Failed to install pip"
            echo "Please install pip manually:"
            echo "  curl https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD"
            exit 1
        }
    fi

    log_success "pip is available"
}

# Create virtual environment
create_venv() {
    if [ "$USE_VENV" = false ]; then
        log_warning "Skipping virtual environment (--no-venv)"
        return
    fi

    log_info "Creating virtual environment..."

    if [ -d "$VENV_DIR" ]; then
        log_warning "Virtual environment already exists at $VENV_DIR"
        read -p "Do you want to recreate it? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            log_info "Using existing virtual environment"
            return
        fi
    fi

    $PYTHON_CMD -m venv "$VENV_DIR"
    log_success "Virtual environment created at $VENV_DIR"
}

# Activate virtual environment
activate_venv() {
    if [ "$USE_VENV" = false ]; then
        return
    fi

    log_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    log_info "Installing VoiceLLAMA..."

    cd "$INSTALL_DIR"

    # Upgrade pip first
    pip install --upgrade pip

    # Install VoiceLLAMA with Kokoro
    if [ "$INSTALL_DEV" = true ]; then
        pip install -e ".[dev,kokoro]"
        log_success "Installed VoiceLLAMA with dev dependencies"
    else
        pip install -e ".[kokoro]"
        log_success "Installed VoiceLLAMA"
    fi
}

# Check for ffmpeg
check_ffmpeg() {
    log_info "Checking for ffmpeg (optional, for MP3/OGG support)..."

    if check_command ffmpeg; then
        log_success "ffmpeg is installed"
    else
        log_warning "ffmpeg not found - MP3/OGG encoding will not be available"
        echo "  To install ffmpeg:"
        echo "    Ubuntu/Debian: sudo apt install ffmpeg"
        echo "    macOS: brew install ffmpeg"
        echo "    Windows: winget install ffmpeg"
    fi
}

# Configure Claude Code hooks
configure_hooks() {
    if [ "$INSTALL_HOOKS" = false ]; then
        log_info "Skipping Claude Code hooks configuration (--no-hooks)"
        return
    fi

    log_info "Configuring Claude Code hooks..."

    CLAUDE_DIR="$HOME/.claude"
    SETTINGS_FILE="$CLAUDE_DIR/settings.json"
    HOOKS_DIR="$INSTALL_DIR/src/voicellama/hooks"

    # Create .claude directory if it doesn't exist
    mkdir -p "$CLAUDE_DIR"

    # Check if settings.json exists
    if [ -f "$SETTINGS_FILE" ]; then
        log_warning "Claude Code settings already exist at $SETTINGS_FILE"
        read -p "Do you want to add VoiceLLAMA hooks to existing settings? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Skipping hooks configuration"
            return
        fi

        # Backup existing settings
        cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "Backed up existing settings"
    fi

    # Generate hooks configuration
    PYTHON_PATH="$VENV_DIR/bin/python3"
    if [ "$USE_VENV" = false ]; then
        PYTHON_PATH="$PYTHON_CMD"
    fi

    # Create or update settings.json using Python
    $PYTHON_CMD << EOF
import json
import os
from pathlib import Path

settings_file = Path("$SETTINGS_FILE")
hooks_dir = Path("$HOOKS_DIR")
python_path = "$PYTHON_PATH"

# Default settings structure
default_settings = {
    "hooks": {}
}

# Load existing settings if they exist
if settings_file.exists():
    try:
        with open(settings_file) as f:
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
with open(settings_file, "w") as f:
    json.dump(settings, f, indent=2)

print(f"Hooks configured in {settings_file}")
EOF

    log_success "Claude Code hooks configured"
}

# Create start script
create_start_script() {
    log_info "Creating start script..."

    START_SCRIPT="$INSTALL_DIR/start-voicellama.sh"

    if [ "$USE_VENV" = true ]; then
        cat > "$START_SCRIPT" << 'EOF'
#!/bin/bash
# VoiceLLAMA Start Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
echo "Starting VoiceLLAMA TTS Server..."
echo "Web UI: http://localhost:8333"
echo "Settings: http://localhost:8333/settings"
echo "Press Ctrl+C to stop"
echo ""
voicellama serve "$@"
EOF
    else
        cat > "$START_SCRIPT" << 'EOF'
#!/bin/bash
# VoiceLLAMA Start Script
echo "Starting VoiceLLAMA TTS Server..."
echo "Web UI: http://localhost:8333"
echo "Settings: http://localhost:8333/settings"
echo "Press Ctrl+C to stop"
echo ""
voicellama serve "$@"
EOF
    fi

    chmod +x "$START_SCRIPT"
    log_success "Created start script: $START_SCRIPT"
}

# Print final instructions
print_instructions() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 Installation Complete!                        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  ./start-voicellama.sh"
    echo ""
    echo -e "${BLUE}Or manually:${NC}"
    if [ "$USE_VENV" = true ]; then
        echo "  source venv/bin/activate"
    fi
    echo "  voicellama serve"
    echo ""
    echo -e "${BLUE}Access the UI:${NC}"
    echo "  Settings: http://localhost:8333"
    echo "  Avatar:   http://localhost:8333/avatar"
    echo ""
    echo -e "${BLUE}API Documentation:${NC}"
    echo "  Health:   http://localhost:8333/v1/health"
    echo "  Voices:   http://localhost:8333/v1/voices"
    echo "  TTS:      POST http://localhost:8333/v1/tts/announce"
    echo ""
    if [ "$INSTALL_HOOKS" = true ]; then
        echo -e "${BLUE}Claude Code Hooks:${NC}"
        echo "  Hooks have been configured in ~/.claude/settings.json"
        echo "  Restart Claude Code for hooks to take effect"
        echo ""
    fi
    echo -e "${YELLOW}Note:${NC} The Kokoro model will be downloaded on first use (~200MB)"
    echo ""
}

# Main installation flow
main() {
    print_banner

    log_info "Starting installation..."
    echo ""

    check_python
    check_pip
    create_venv
    activate_venv
    install_dependencies
    check_ffmpeg
    configure_hooks
    create_start_script

    print_instructions

    if [ "$START_SERVER" = true ]; then
        log_info "Starting VoiceLLAMA server..."
        exec voicellama serve
    fi
}

# Run main
main
