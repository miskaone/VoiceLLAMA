# Starting VoiceLLAMA Server

## Quick Start

### Option 1: Using the venv directly (Recommended)

**PowerShell:**
```powershell
# Navigate to project directory
cd c:\dev\VoiceLLAMA\voicellama

# Activate venv
.\venv\Scripts\Activate.ps1

# Start server
python -m voicellama serve
```

**CMD:**
```cmd
cd c:\dev\VoiceLLAMA\voicellama
venv\Scripts\activate.bat
python -m voicellama serve
```

### Option 2: Using the startup script

**PowerShell:**
```powershell
.\run_server.ps1
```

**CMD:**
```cmd
run_server.bat
```

### Option 3: Direct uvicorn (if imports fail)

```powershell
cd c:\dev\VoiceLLAMA\voicellama
.\venv\Scripts\python.exe -m uvicorn server.app:app --host 0.0.0.0 --port 8333 --reload
```

**Note:** This may require fixing imports in the code to use relative imports instead of `voicellama.` prefix.

## Server URLs

Once started, the server will be available at:
- **API**: http://localhost:8333
- **Health Check**: http://localhost:8333/health
- **API Documentation**: http://localhost:8333/docs
- **Settings UI**: http://localhost:8333/settings
- **Avatar UI**: http://localhost:8333/avatar

## Troubleshooting

### If you get "ModuleNotFoundError: No module named 'voicellama'"

The editable install may not be working correctly. Try:

```powershell
# Reinstall in editable mode
.\venv\Scripts\pip.exe install -e .
```

### If server doesn't start

1. Check if port 8333 is already in use:
   ```powershell
   netstat -an | Select-String "8333"
   ```

2. Try a different port:
   ```powershell
   python -m voicellama serve --port 9000
   ```

3. Check for errors in the console output

### First Run Notes

- On first run, Kokoro will download models (this may take a few minutes)
- The server will be slower on first request as it loads the pipeline
- Subsequent requests will be faster

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

