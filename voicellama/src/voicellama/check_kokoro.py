#!/usr/bin/env python3
"""Quick script to check if Kokoro is installed and working."""

import sys

def check_kokoro():
    """Check if Kokoro is installed and can be imported."""
    print("Checking Kokoro installation...")
    print("-" * 50)
    
    # Check 1: Try importing kokoro
    try:
        import kokoro
        print("[OK] kokoro module imported successfully")
        
        # Show location
        if hasattr(kokoro, '__file__'):
            print(f"  Location: {kokoro.__file__}")
        
        # Show version if available
        version = getattr(kokoro, '__version__', None)
        if version:
            print(f"  Version: {version}")
        else:
            print("  Version: unknown")
            
    except ImportError as e:
        print(f"[FAIL] kokoro module NOT found")
        print(f"  Error: {e}")
        print("\nTo install Kokoro:")
        print("  pip install kokoro")
        print("  or: pip install -e '.[kokoro]'")
        return False
    
    # Check 2: Try importing KPipeline
    try:
        from kokoro import KPipeline
        print("[OK] KPipeline class imported successfully")
    except ImportError as e:
        print(f"[FAIL] KPipeline class NOT available")
        print(f"  Error: {e}")
        return False
    
    # Check 3: Try creating a pipeline instance (optional - this might download models)
    try:
        print("\nAttempting to create KPipeline instance...")
        print("(This may download models on first run)")
        pipeline = KPipeline(lang_code='a')
        print("[OK] KPipeline instance created successfully")
        return True
    except Exception as e:
        print(f"[WARN] KPipeline instance creation failed")
        print(f"  Error: {e}")
        print("  (This might be okay if models need to be downloaded)")
        return False

if __name__ == "__main__":
    success = check_kokoro()
    print("-" * 50)
    if success:
        print("\n[SUCCESS] Kokoro is properly installed and ready to use!")
        sys.exit(0)
    else:
        print("\n[FAIL] Kokoro installation check failed")
        sys.exit(1)

