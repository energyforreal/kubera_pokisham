"""Singleton lock mechanism to prevent multiple trading agent instances."""

import os
import sys
from pathlib import Path


class SingletonLock:
    """Ensure only one instance of trading agent runs at a time."""
    
    def __init__(self, lockfile=".trading_agent.lock"):
        self.lockfile = Path(lockfile)
        self.acquired = False
    
    def acquire(self):
        """Acquire lock or exit if already locked."""
        if self.lockfile.exists():
            try:
                with open(self.lockfile, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is still running (Windows-compatible)
                try:
                    if sys.platform == "win32":
                        # On Windows, use tasklist to check if process exists
                        import subprocess
                        result = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}'],
                            capture_output=True,
                            text=True
                        )
                        if str(pid) in result.stdout:
                            print(f"❌ Trading agent already running (PID: {pid})")
                            print("⚠️  Stop the existing instance before starting a new one.")
                            print(f"   Use: taskkill /F /PID {pid}")
                            sys.exit(1)
                        else:
                            # Process doesn't exist, remove stale lockfile
                            print(f"🧹 Removing stale lockfile (PID {pid} not running)")
                            self.lockfile.unlink()
                    else:
                        # On Unix-like systems, use kill signal 0
                        os.kill(pid, 0)
                        print(f"❌ Trading agent already running (PID: {pid})")
                        print("⚠️  Stop the existing instance before starting a new one.")
                        print(f"   Use: kill {pid}")
                        sys.exit(1)
                except (OSError, subprocess.SubprocessError):
                    # Process doesn't exist, remove stale lockfile
                    print(f"🧹 Removing stale lockfile (PID {pid} not running)")
                    self.lockfile.unlink()
            except (ValueError, FileNotFoundError):
                # Invalid lockfile, remove it
                self.lockfile.unlink()
        
        # Create lockfile with current PID
        with open(self.lockfile, 'w') as f:
            f.write(str(os.getpid()))
        
        self.acquired = True
        print(f"🔒 Singleton lock acquired (PID: {os.getpid()})")
    
    def release(self):
        """Release lock."""
        if self.acquired and self.lockfile.exists():
            try:
                self.lockfile.unlink()
                print(f"🔓 Singleton lock released")
            except OSError as e:
                print(f"Warning: Could not remove lock file: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
        return False

