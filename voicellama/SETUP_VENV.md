# Setting Up Virtual Environment with Python 3.12

## Step 1: Install Python 3.12 (if not already installed)

If Python 3.12 is not installed, you can:

### Option A: Download from python.org
1. Go to https://www.python.org/downloads/
2. Download Python 3.12.x (latest 3.12 version)
3. During installation, check "Add Python to PATH"

### Option B: Use Windows Store
```powershell
# Open Microsoft Store and search for "Python 3.12"
# Or use winget (if available)
winget install Python.Python.3.12
```

### Option C: Use py launcher to install
```powershell
# Set environment variable to allow auto-install
$env:PYLAUNCHER_ALLOW_INSTALL=1
py -3.12 --version  # This will prompt to install if not found
```

## Step 2: Create Virtual Environment

Once Python 3.12 is available:

```powershell
# Navigate to project directory
cd c:\dev\VoiceLLAMA\voicellama

# Create venv with Python 3.12
py -3.12 -m venv venv

# Or if python3.12 is in PATH:
python3.12 -m venv venv
```

## Step 3: Activate Virtual Environment

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Windows CMD
venv\Scripts\activate.bat
```

## Step 4: Install Dependencies

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install voicellama with Kokoro
pip install -e ".[kokoro]"

# Or install separately:
pip install -e .
pip install kokoro
```

## Step 5: Verify Installation

```powershell
# Check Python version
python --version  # Should show Python 3.12.x

# Check Kokoro
python check_kokoro.py

# Run tests
pytest -m "not benchmark"
```

## Troubleshooting

### If Python 3.12 is not found:
- Make sure Python 3.12 is installed
- Check PATH environment variable includes Python 3.12
- Try using full path: `C:\Python312\python.exe -m venv venv`

### If activation fails:
- PowerShell execution policy: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Use CMD instead: `venv\Scripts\activate.bat`

### If Kokoro installation fails:
- Try installing Kokoro separately first: `pip install kokoro`
- Check if you have Visual Studio Build Tools installed (for C extensions)
- Consider using conda which includes compilers

