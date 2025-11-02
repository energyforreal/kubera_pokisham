#!/usr/bin/env python3
"""
Script to restart the trading agent properly
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    """Restart the trading agent."""
    print("🔄 Restarting Trading Agent...")
    
    # Kill existing Python processes (trading agent)
    try:
        print("🛑 Stopping existing trading agent processes...")
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "python3.12.exe"], capture_output=True)
        time.sleep(2)
    except Exception as e:
        print(f"Warning: Could not stop existing processes: {e}")
    
    # Clear any lock files
    lock_file = Path(".trading_agent.lock")
    if lock_file.exists():
        lock_file.unlink()
        print("🔓 Cleared lock file")
    
    # Start the trading agent
    print("🚀 Starting trading agent...")
    try:
        # Start in a new window
        subprocess.Popen([
            "cmd", "/c", "start", "Trading Agent", "python", "src/main.py"
        ], cwd=os.getcwd())
        print("✅ Trading agent started in new window")
        print("⏳ Please wait 30 seconds for the agent to initialize...")
        
    except Exception as e:
        print(f"❌ Failed to start trading agent: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
