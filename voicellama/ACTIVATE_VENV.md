# Virtual Environment Created! 🎉

## Virtual Environment Status

✅ **Virtual environment created with Python 3.11.9**

## Next Steps

### 1. Activate the Virtual Environment

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**CMD:**
```cmd
venv\Scripts\activate.bat
```

### 2. Verify Activation

After activation, you should see `(venv)` in your prompt:
```powershell
(venv) PS C:\dev\VoiceLLAMA\voicellama>
```

Verify Python version:
```powershell
python --version  # Should show Python 3.11.9
```

### 3. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 4. Install VoiceLLAMA with Kokoro

```powershell
# Install voicellama in editable mode with Kokoro
pip install -e ".[kokoro]"
```

### 5. Verify Installation

```powershell
# Check if Kokoro is installed
python check_kokoro.py

# Run tests
pytest -m "not benchmark"
```

## Note About Python 3.12

You requested Python 3.12, but Python 3.11.9 is installed and will work perfectly fine. Python 3.11 has excellent compatibility with Kokoro and all its dependencies.

If you still want Python 3.12:
1. Download from https://www.python.org/downloads/
2. Install Python 3.12
3. Create a new venv: `py -3.12 -m venv venv312`

## Deactivating

When you're done, deactivate the venv:
```powershell
deactivate
```

