#!/usr/bin/env python3
"""Start VoiceLLAMA server."""

import sys
import os

# Get project root (directory containing this script)
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, "src")

# Add src directory to Python path (where voicellama package lives)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Change to project root directory
os.chdir(project_root)

try:
    # Now imports should work (voicellama package is in src/)
    from voicellama.server import create_app
    from voicellama.config import Config
    import uvicorn
    
    config = Config.load()
    
    print(f"Starting VoiceLLAMA server on http://{config.server.host}:{config.server.port}")
    print(f"Python: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    
    app = create_app(config)
    
    print("Server starting...")
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        log_level=config.server.log_level.lower()
    )
except Exception as e:
    print(f"Error starting server: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

