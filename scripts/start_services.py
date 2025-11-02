#!/usr/bin/env python3
"""
Service Startup Script
Starts all required services for validation.
"""

import subprocess
import time
import sys
import requests
import json
from pathlib import Path

def start_trading_agent():
    """Start the trading agent."""
    print("🤖 Starting trading agent...")
    try:
        # Start trading agent in background
        process = subprocess.Popen([
            sys.executable, 'src/main.py'
        ], cwd=Path(__file__).parent.parent)
        
        print("✅ Trading agent started (PID: {})".format(process.pid))
        return process
    except Exception as e:
        print(f"❌ Failed to start trading agent: {e}")
        return None

def start_backend_api():
    """Start the backend API."""
    print("🔧 Starting backend API...")
    try:
        # Start backend API in background
        process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 'api.main:app',
            '--host', '0.0.0.0', '--port', '8000'
        ], cwd=Path(__file__).parent.parent / 'backend')
        
        print("✅ Backend API started (PID: {})".format(process.pid))
        return process
    except Exception as e:
        print(f"❌ Failed to start backend API: {e}")
        return None

def wait_for_trading_agent(max_wait=30):
    """Wait for trading agent to be ready."""
    print("⏳ Waiting for trading agent to be ready...")
    
    for i in range(max_wait):
        try:
            health_file = Path('bot_health.json')
            if health_file.exists():
                with open(health_file) as f:
                    health_data = json.load(f)
                    if health_data.get('status') == 'healthy':
                        print("✅ Trading agent is healthy")
                        return True
        except:
            pass
        
        if i % 5 == 0 and i > 0:
            print(f"   Still waiting... ({i}/{max_wait}s)")
        
        time.sleep(1)
    
    print("⚠️  Trading agent may not be ready")
    return False

def wait_for_backend_api(max_wait=30):
    """Wait for backend API to be ready."""
    print("⏳ Waiting for backend API to be ready...")
    
    for i in range(max_wait):
        try:
            response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
            if response.status_code == 200:
                print("✅ Backend API is responding")
                return True
        except:
            pass
        
        if i % 5 == 0 and i > 0:
            print(f"   Still waiting... ({i}/{max_wait}s)")
        
        time.sleep(1)
    
    print("⚠️  Backend API may not be ready")
    return False

def check_services():
    """Check if services are already running."""
    print("🔍 Checking if services are already running...")
    
    # Check trading agent
    trading_agent_running = False
    try:
        health_file = Path('bot_health.json')
        if health_file.exists():
            with open(health_file) as f:
                health_data = json.load(f)
                if health_data.get('status') == 'healthy':
                    trading_agent_running = True
                    print("✅ Trading agent is already running")
    except:
        pass
    
    # Check backend API
    backend_api_running = False
    try:
        response = requests.get('http://localhost:8000/api/v1/health', timeout=5)
        if response.status_code == 200:
            backend_api_running = True
            print("✅ Backend API is already running")
    except:
        pass
    
    return trading_agent_running, backend_api_running

def main():
    """Main function."""
    print("🚀 Starting KUBERA POKISHAM services...")
    print("=" * 50)
    
    # Check if services are already running
    trading_agent_running, backend_api_running = check_services()
    
    processes = []
    
    # Start trading agent if not running
    if not trading_agent_running:
        process = start_trading_agent()
        if process:
            processes.append(('trading_agent', process))
    else:
        print("🤖 Trading agent already running")
    
    # Start backend API if not running
    if not backend_api_running:
        process = start_backend_api()
        if process:
            processes.append(('backend_api', process))
    else:
        print("🔧 Backend API already running")
    
    if not processes:
        print("✅ All services are already running!")
        return
    
    # Wait for services to be ready
    print("\n⏳ Waiting for services to be ready...")
    
    if not trading_agent_running:
        wait_for_trading_agent()
    
    if not backend_api_running:
        wait_for_backend_api()
    
    print("\n✅ All services started successfully!")
    print("🔍 You can now run validation scripts:")
    print("   python scripts/check_integrations.py")
    print("   python scripts/validate_sync.py")
    print("   python scripts/test_realtime.py")
    print("   python scripts/check_data_consistency.py")
    
    # Keep processes running
    try:
        print("\n🔄 Services are running. Press Ctrl+C to stop all services...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except:
                try:
                    process.kill()
                    print(f"✅ {name} force stopped")
                except:
                    print(f"❌ Failed to stop {name}")

if __name__ == "__main__":
    main()
