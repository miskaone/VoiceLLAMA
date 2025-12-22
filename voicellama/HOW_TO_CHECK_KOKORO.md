# How to Check if Kokoro is Installed

## Quick Check Methods

### Method 1: Python Import Test
```bash
python -c "import kokoro; print('Kokoro is installed')"
```

If Kokoro is installed, you'll see: `Kokoro is installed`  
If not, you'll see: `ModuleNotFoundError: No module named 'kokoro'`

### Method 2: Check with pip
```bash
pip show kokoro
```

If installed, shows package info. If not: `WARNING: Package(s) not found: kokoro`

### Method 3: List all packages
```bash
pip list | findstr kokoro
```

Shows kokoro in the list if installed.

### Method 4: Use the check script
```bash
python check_kokoro.py
```

This script will:
- Check if kokoro module can be imported
- Check if KPipeline class is available
- Optionally test creating a pipeline instance

### Method 5: Test from within VoiceLLAMA
```python
from voicellama.server.routes.tts import load_pipeline
try:
    pipeline = load_pipeline()
    print("Kokoro is installed and working!")
except ImportError as e:
    print(f"Kokoro not installed: {e}")
```

## Current Status

Based on the checks:
- **Kokoro is NOT currently installed** in your Python environment
- The tests work because they use mocks (`mock_pipeline` fixture)
- If you want to run the actual TTS server, you'll need to install Kokoro

## Installing Kokoro

```bash
# Option 1: Install with optional dependencies
pip install -e ".[kokoro]"

# Option 2: Install Kokoro separately
pip install kokoro
```

## Verifying Installation

After installing, run:
```bash
python check_kokoro.py
```

Or test directly:
```bash
python -c "from kokoro import KPipeline; print('Success!')"
```

